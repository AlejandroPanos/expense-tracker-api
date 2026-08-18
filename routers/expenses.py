# Imports
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Category, Expense
from routers.auth import get_current_user
from pydantic import BaseModel, Field, field_validator
from datetime import date as date_type

# Router
router = APIRouter(prefix="/expenses", tags=["expenses"])


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# Request classes
class CreateExpenseRequest(BaseModel):
    amount: float = Field(gt=0)
    description: str = Field(max_length=150)
    date: date_type
    category_id: int

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, value):
        if value > date_type.today():
            raise ValueError("Expense cannot be in the future.")
        return value


# Endpoints
@router.post("/", status_code=status.HTTP_200_OK)
async def create_expense(
    db: db_dependency, user: user_dependency, expense_request: CreateExpenseRequest
):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    category = (
        db.query(Category)
        .filter(
            Category.id == expense_request.category_id,
            Category.owner_id == user.get("id"),
        )
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found or does not belong to user",
        )

    expense = Expense(
        amount=expense_request.amount,
        description=expense_request.description,
        date=expense_request.date,
        owner_id=user.get("id"),
        category_id=expense_request.category_id,
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    return expense
