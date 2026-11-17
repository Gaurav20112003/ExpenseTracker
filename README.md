# AI Expense Tracker

This project is a small personal expense-tracking application built with FastAPI. It lets you describe an expense in plain English (for example, “Lunch at Cafe Express, ₹420 today”), then uses Google Gemini to extract the amount, currency, merchant, category, description, and date before saving it to a local SQLite database.

## What the app does

- Accepts a natural-language expense description from the browser or API
- Uses Gemini AI to normalize the text into structured data
- Stores the expense locally in SQLite
- Shows a timeline of recorded expenses in the UI
- Lets you filter expenses by date and delete entries
- Exposes a small REST API for automation or future integrations

## Tech stack

- Backend: FastAPI
- Database: SQLite
- AI parsing: Google Gemini API
- Frontend: simple HTML/CSS/JavaScript served by FastAPI

## Project structure

```text
Expense_Tracker/
├── app/
│   ├── main.py             # FastAPI app startup
│   ├── routes.py           # Expense API routes
│   ├── database.py         # SQLite access helpers
│   ├── services.py         # Gemini parsing logic
│   ├── auth.py             # Token validation hook
│   ├── models.py           # Pydantic request/response models
│   ├── static/
│   │   ├── app.js          # Frontend interaction logic
│   │   └── styles.css      # UI styling
│   └── templates/
│       └── index.html      # Main page
├── data/
│   └── expenses.sqlite3    # Local database file
├── tests/
├── .env.example            # Optional env template (if present in your environment)
├── Dockerfile
├── requirements.txt
├── README.md
└── .gitignore
```

## Features

### AI-powered expense capture

The app is designed for quick input. Instead of asking the user to fill in multiple fields manually, it accepts a single freeform sentence and infers:

- amount
- currency
- category
- merchant
- date
- description

Accepted categories are currently limited to:

- Food
- Travel
- Software
- Office
- Other

### Local-first storage

Expense records are saved locally in `data/expenses.sqlite3` by default. This makes the app easy to run and test without external services beyond the Gemini API.

### Browser-based UI

The main page offers:

- a text area for entering an expense description
- automatic AI parsing on submit
- list of saved expenses
- date filter for historical view
- delete action for removing incorrect entries

## Local setup

1. Create and activate a virtual environment if needed.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file at the project root or export the environment variable:

```bash
GEMINI_API_KEY=your_google_gemini_api_key
```

4. Start the app:

```bash
uvicorn app.main:app --reload
```

5. Open the app in your browser:

```text
http://127.0.0.1:8000
```

## Environment variables

- `GEMINI_API_KEY`: required for AI parsing using the Gemini API
- `EXPENSE_DB_PATH`: optional override for the SQLite database path

If you do not set `EXPENSE_DB_PATH`, the app uses:

```text
data/expenses.sqlite3
```

## Docker

The app includes a Dockerfile for containerized deployment. For local persistence, mount a named volume on `/app/data` so the database survives container restarts:

```bash
docker run -p 8000:8000 -e GEMINI_API_KEY -v expense-data:/app/data expense-tracker
```

## API overview

The main API routes are under `/api/v1`:

- `POST /api/v1/expenses` — parses and saves an expense
- `GET /api/v1/expenses` — lists all expenses or filters by date using `?expense_day=YYYY-MM-DD`
- `DELETE /api/v1/expenses/{id}` — removes an expense by ID

Example request body:

```json
{
  "text": "Bought groceries worth $42.50 at Whole Foods on 2026-11-01"
}
```

## Notes

- The code currently keeps the app local and simple; it is a good base for extending with reporting, monthly summaries, or category analytics.
- The authentication hook in `app/auth.py` is intentionally permissive and can be replaced with a real token check when the app is deployed beyond local use.
- The app should run with a valid Gemini API key and network access to the Generative Language API.
