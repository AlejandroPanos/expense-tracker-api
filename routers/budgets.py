# Imports
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Budget, Category
from routers.auth import get_current_user
from pydantic import BaseModel, Field, field_validator
from datetime import date as date_type

# Router
router = APIRouter(prefix="/budgets", tags=["budgets"])


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
class CreateBudgetRequest(BaseModel):
    category_id: int
    monthly_limit: float = Field(gt=0)


# Endpoints
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_budget(
    db: db_dependency, user: user_dependency, budget_request: CreateBudgetRequest
):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    category = (
        db.query(Category)
        .filter(
            Category.id == budget_request.category_id,
            Category.owner_id == user.get("id"),
        )
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found or does not belong to user",
        )

    budget = Budget(
        owner_id=user.get("id"),
        category_id=budget_request.category_id,
        monthly_limit=budget_request.monthly_limit,
    )

    db.add(budget)
    db.commit()
    db.refresh(budget)

    return budget


@router.get("/", status_code=status.HTTP_200_OK)
async def get_budget_list(
    db: db_dependency, user: user_dependency, skip: int = 0, limit: int = 0
):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    budget_list = db.query(Budget).filter(Budget.owner_id == user.get("id"))

    if budget_list is None:
        raise HTTPException(status_code=404, detail="Budgets not found for user")

    return budget_list.offset(skip).limit(limit).all()
