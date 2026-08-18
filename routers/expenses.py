# Imports
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
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


class UpdateExpenseRequest(BaseModel):
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


@router.get("/summary", status_code=status.HTTP_200_OK)
async def get_expenses_by_category(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    results = (
        db.query(
            Category.name,
            func.sum(Expense.amount).label("total_spent"),
        )
        .join(Category, Expense.category_id == Category.id)
        .filter(Expense.owner_id == user.get("id"))
        .group_by(Category.name)
        .all()
    )

    return [{"category": name, "total_spent": total} for name, total in results]


@router.get("/{expense_id}", status_code=status.HTTP_200_OK)
async def get_expense_by_id(db: db_dependency, user: user_dependency, expense_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    expense = db.query(Expense).filter(Expense.id == expense_id).first()

    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    return expense


@router.put("/{expense_id}", status_code=status.HTTP_200_OK)
async def update_expense_by_id(
    db: db_dependency,
    user: user_dependency,
    expense_id: int,
    update_request: UpdateExpenseRequest,
):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    expense = db.query(Expense).filter(Expense.id == expense_id).first()

    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    category = (
        db.query(Category)
        .filter(
            Category.id == update_request.category_id,
            Category.owner_id == user.get("id"),
        )
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found or does not belong to user",
        )

    expense.amount = update_request.amount
    expense.description = update_request.description
    expense.date = update_request.date
    expense.category_id = update_request.category_id

    db.add(expense)
    db.commit()
    db.refresh(expense)

    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_200_OK)
async def delete_expense(db: db_dependency, user: user_dependency, expense_id: str):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    expense_model = db.query(Expense).filter(Expense.id == expense_id).first()

    if expense_model is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    if expense_model.owner_id != user.get("id"):
        raise HTTPException(status_code=401, detail="User not authorised")

    db.query(Expense).filter(Expense.id == expense_id).delete()

    db.commit()

    return {"message": "Expense deleted successfully"}
