# Imports
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Category, Expense, Budget
from .auth import get_current_user

# Router
router = APIRouter(prefix="/categories", tags=["categories"])


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
class NewCategoryRequest(BaseModel):
    name: str


class UpdateCategoryRequest(BaseModel):
    new_name: str = Field(min_length=1, max_length=20)


# Endpoints
@router.get("/", status_code=status.HTTP_200_OK)
async def get_categories(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    user_categories = (
        db.query(Category).filter(Category.owner_id == user.get("id")).all()
    )

    return user_categories


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_category(
    db: db_dependency, user: user_dependency, category_request: NewCategoryRequest
):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    existing = (
        db.query(Category)
        .filter(
            Category.owner_id == user.get("id"), Category.name == category_request.name
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    category = Category(name=category_request.name, owner_id=user.get("id"))

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.get("/{category_id}", status_code=status.HTTP_200_OK)
async def get_category_by_id(
    db: db_dependency, user: user_dependency, category_id: int
):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    category_model = db.query(Category).filter(Category.id == category_id).first()

    if category_model is None:
        raise HTTPException(status_code=404, detail="Category not found")

    if category_model.owner_id != user.get("id"):
        raise HTTPException(status_code=401, detail="User not authorised")

    return category_model


@router.put("/{category_id}", status_code=status.HTTP_200_OK)
async def update_category(
    db: db_dependency,
    user: user_dependency,
    category_request: UpdateCategoryRequest,
    category_id: int,
):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    category_model = db.query(Category).filter(Category.id == category_id).first()

    if category_model is None:
        raise HTTPException(status_code=404, detail="Category not found")

    if category_model.owner_id != user.get("id"):
        raise HTTPException(status_code=401, detail="User not authorised")

    category_model.name = category_request.new_name

    db.add(category_model)
    db.commit()
    db.refresh(category_model)

    return category_model


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(db: db_dependency, user: user_dependency, category_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    category_model = db.query(Category).filter(Category.id == category_id).first()

    if category_model is None:
        raise HTTPException(status_code=404, detail="Category not found")

    if category_model.owner_id != user.get("id"):
        raise HTTPException(status_code=401, detail="User not authorised")

    expense_count = db.query(Expense).filter(Expense.category_id == category_id).count()
    budget_count = db.query(Budget).filter(Budget.category_id == category_id).count()

    if expense_count > 0 or budget_count > 0:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot delete category: {expense_count} expense(s) and "
                f"{budget_count} budget(s) are still linked to it. "
                "Delete or reassign them first."
            ),
        )

    db.query(Category).filter(Category.id == category_id).delete()

    db.commit()

    return {"message": "Category deleted successfully"}
