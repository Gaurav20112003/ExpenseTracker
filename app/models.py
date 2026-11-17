from datetime import date, datetime

from pydantic import BaseModel, Field


class ExpenseRequest(BaseModel):
    text: str = Field(min_length=1, description="Natural-language description of an expense")


class ExpenseDetails(BaseModel):
    amount: float = Field(gt=0)
    currency: str
    category: str
    merchant: str
    description: str
    date: date


class ExpenseResponse(ExpenseDetails):
    id: int
    created_at: datetime
