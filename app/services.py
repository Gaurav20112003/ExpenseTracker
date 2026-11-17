import asyncio
import json
import os
import time
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()


class GeminiAPIError(Exception):
    pass


_TRANSIENT_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_GEMINI_ATTEMPTS = 4


async def parse_expense_with_ai(text: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-3.5-flash-lite:generateContent"
    )
    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "Extract expense details from the user's input. "
                        "Categorize strictly as Food, Travel, Software, Office, "
                        "or Other. Return amount, currency, category, merchant, "
                        "description, and date in YYYY-MM-DD format."
                    )
                }
            ]
        },
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "amount": {"type": "NUMBER"},
                    "currency": {"type": "STRING"},
                    "category": {
                        "type": "STRING",
                        "enum": ["Food", "Travel", "Software", "Office", "Other"],
                    },
                    "merchant": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "date": {"type": "STRING"},
                },
                "required": [
                    "amount",
                    "currency",
                    "category",
                    "merchant",
                    "description",
                    "date",
                ],
            },
        },
    }

    def request_gemini() -> dict:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
        )
        for attempt in range(_MAX_GEMINI_ATTEMPTS):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                if exc.code not in _TRANSIENT_HTTP_STATUS_CODES:
                    raise GeminiAPIError(
                        f"Gemini returned HTTP {exc.code}."
                    ) from exc
                if attempt == _MAX_GEMINI_ATTEMPTS - 1:
                    raise GeminiAPIError(
                        "Gemini is temporarily unavailable after "
                        f"{_MAX_GEMINI_ATTEMPTS} attempts (HTTP {exc.code}). "
                        "Please try again shortly."
                    ) from exc

                retry_after = (
                    exc.headers.get("Retry-After") if exc.headers else None
                )
                try:
                    delay = max(0.0, min(float(retry_after), 10.0))
                except (TypeError, ValueError):
                    delay = 2**attempt
                time.sleep(delay)
            except (urllib.error.URLError, TimeoutError) as exc:
                raise GeminiAPIError("Could not connect to the Gemini API.") from exc

        try:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(raw_text)
        except (
            KeyError,
            IndexError,
            TypeError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError("Gemini returned an invalid expense response.") from exc

        if not isinstance(result, dict):
            raise ValueError("Gemini returned an invalid expense response.")

        return result

    return await asyncio.to_thread(request_gemini)
