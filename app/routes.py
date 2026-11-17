import sqlite3
from datetime import date
from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import verify_token
from app import database
from app.models import ExpenseDetails, ExpenseRequest, ExpenseResponse
from app.services import GeminiAPIError, parse_expense_with_ai

router = APIRouter(prefix="/api/v1", tags=["expenses"])
logger = getLogger(__name__)


@router.post(
    "/expenses",
    response_model=ExpenseResponse,
    dependencies=[Depends(verify_token)],
)
async def create_expense(request: ExpenseRequest) -> ExpenseResponse:
    try:
        parsed_expense = ExpenseDetails.model_validate(
            await parse_expense_with_ai(request.text)
        )
    except GeminiAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    try:
        return database.save_expense(parsed_expense)
    except sqlite3.Error as exc:
        logger.exception("Could not save parsed expense")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the expense.",
        ) from exc


@router.get(
    "/expenses",
    response_model=list[ExpenseResponse],
    dependencies=[Depends(verify_token)],
)
async def get_expenses(expense_day: date | None = None) -> list[ExpenseResponse]:
    try:
        return database.list_expenses(expense_day)
    except sqlite3.Error as exc:
        logger.exception("Could not load expenses")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load expenses.",
        ) from exc


@router.delete(
    "/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_token)],
)
async def remove_expense(expense_id: int) -> None:
    try:
        deleted = database.delete_expense(expense_id)
    except sqlite3.Error as exc:
        logger.exception("Could not delete expense %s", expense_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete the expense.",
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found.",
        )
