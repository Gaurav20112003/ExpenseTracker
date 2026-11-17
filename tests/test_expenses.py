import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app import database
from app.main import app


class ExpenseApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "expenses.sqlite3"
        self.database_path_patch = patch.object(database, "DB_PATH", self.database_path)
        self.database_path_patch.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.parse_expense = patch(
            "app.routes.parse_expense_with_ai",
            new_callable=AsyncMock,
            return_value={
                "amount": 12.5,
                "currency": "USD",
                "category": "Food",
                "merchant": "Corner Cafe",
                "description": "Lunch",
                "date": "2026-11-17",
            },
        )
        self.parse_expense.start()

    def tearDown(self) -> None:
        self.parse_expense.stop()
        self.client.__exit__(None, None, None)
        self.database_path_patch.stop()
        self.temp_dir.cleanup()

    def test_create_and_filter_persisted_expense(self) -> None:
        created = self.client.post(
            "/api/v1/expenses", json={"text": "lunch at the cafe"}
        )
        self.assertEqual(created.status_code, 200)
        saved = created.json()
        self.assertEqual(saved["merchant"], "Corner Cafe")
        self.assertTrue(saved["created_at"])

        all_expenses = self.client.get("/api/v1/expenses")
        self.assertEqual([item["id"] for item in all_expenses.json()], [saved["id"]])

        matching_day = self.client.get(
            "/api/v1/expenses", params={"expense_day": "2026-11-17"}
        )
        other_day = self.client.get(
            "/api/v1/expenses", params={"expense_day": "2026-11-16"}
        )
        self.assertEqual(len(matching_day.json()), 1)
        self.assertEqual(other_day.json(), [])

    def test_delete_expense_and_report_missing_id(self) -> None:
        created = self.client.post(
            "/api/v1/expenses", json={"text": "lunch at the cafe"}
        ).json()

        deleted = self.client.delete(f"/api/v1/expenses/{created['id']}")
        missing = self.client.delete(f"/api/v1/expenses/{created['id']}")

        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(self.client.get("/api/v1/expenses").json(), [])

    def test_frontend_is_served(self) -> None:
        page = self.client.get("/")
        script = self.client.get("/static/app.js")

        self.assertEqual(page.status_code, 200)
        self.assertIn("Expense history", page.text)
        self.assertEqual(script.status_code, 200)
