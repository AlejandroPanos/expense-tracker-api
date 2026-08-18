# Imports
from typing import Annotated, Optional
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


@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_expenses(
    db: db_dependency,
    user: user_dependency,
    category_id: Optional[int] = None,
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    query = db.query(Expense).filter(Expense.owner_id == user.get("id"))

    if category_id is not None:
        query = query.filter(Expense.category_id == category_id)
    if start_date is not None:
        query = query.filter(Expense.date >= start_date)
    if end_date is not None:
        query = query.filter(Expense.date <= end_date)
    if min_amount is not None:
        query = query.filter(Expense.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Expense.amount <= max_amount)

    return query.offset(skip).limit(limit).all()


@router.get("/{expense_id}", status_code=status.HTTP_200_OK)
async def get_expense_by_id(db: db_dependency, user: user_dependency, expense_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    expense = db.query(Expense).filter(Expense.id == expense_id).first()

    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    return expense
