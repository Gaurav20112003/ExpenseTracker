# Expense Tracker

Expense Tracker is a FastAPI app with a small web interface for entering expenses in plain language. Expense details are extracted by Gemini and stored in a local SQLite database. The history page can filter by expense date, shows when each expense was recorded, and allows deletion.

## Run locally

1. Install the dependencies with `pip install -r requirements.txt`.
2. Set `GEMINI_API_KEY` in the environment (or in a local `.env` file).
3. Start the server with `uvicorn app.main:app --reload`.
4. Open `http://127.0.0.1:8000`.

The database is created automatically at `data/expenses.sqlite3`. Set `EXPENSE_DB_PATH` to use another file. Keep the configured file on persistent storage when deploying in a container.

For Docker, mount a named volume at `/app/data`, for example:

```powershell
docker run -p 8000:8000 -e GEMINI_API_KEY -v expense-data:/app/data expense-tracker
```

The API is available under `/api/v1/expenses`: `POST` parses and saves an expense, `GET` lists expenses (optionally filtered with `?expense_day=YYYY-MM-DD`), and `DELETE /{id}` removes one.
