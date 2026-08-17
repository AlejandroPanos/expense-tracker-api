# Imports
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Category, Users
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


# Endpoints
@router.get("/", status_code=status.HTTP_200_OK)
async def get_categories(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    user_categories = (
        db.query(Category).filter(Category.owner_id == user.get("id")).all()
    )

    return user_categories
