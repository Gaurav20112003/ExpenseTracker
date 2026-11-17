import os
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path

from app.models import ExpenseDetails


_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "expenses.sqlite3"
DB_PATH = Path(os.getenv("EXPENSE_DB_PATH", _DEFAULT_DB_PATH)).expanduser()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=10)


def initialize_database() -> None:
    with closing(_connect()) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL CHECK (amount > 0),
                    currency TEXT NOT NULL,
                    category TEXT NOT NULL,
                    merchant TEXT NOT NULL,
                    description TEXT NOT NULL,
                    expense_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_expenses_date_time "
                "ON expenses (expense_date DESC, created_at DESC)"
            )


def save_expense(expense: ExpenseDetails) -> dict:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    values = (
        expense.amount,
        expense.currency,
        expense.category,
        expense.merchant,
        expense.description,
        expense.date.isoformat(),
        created_at,
    )

    with closing(_connect()) as connection:
        connection.row_factory = sqlite3.Row
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO expenses (
                    amount, currency, category, merchant, description,
                    expense_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            row = connection.execute(
                "SELECT * FROM expenses WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()

    return _row_to_expense(row)


def list_expenses(expense_day: date | None = None) -> list[dict]:
    with closing(_connect()) as connection:
        connection.row_factory = sqlite3.Row
        if expense_day is None:
            rows = connection.execute(
                "SELECT * FROM expenses "
                "ORDER BY expense_date DESC, created_at DESC, id DESC"
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM expenses WHERE expense_date = ? "
                "ORDER BY created_at DESC, id DESC",
                (expense_day.isoformat(),),
            ).fetchall()

    return [_row_to_expense(row) for row in rows]


def delete_expense(expense_id: int) -> bool:
    with closing(_connect()) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM expenses WHERE id = ?", (expense_id,)
            )
    return cursor.rowcount > 0


def _row_to_expense(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "amount": row["amount"],
        "currency": row["currency"],
        "category": row["category"],
        "merchant": row["merchant"],
        "description": row["description"],
        "date": row["expense_date"],
        "created_at": row["created_at"],
    }
