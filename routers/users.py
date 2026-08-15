from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from auth import get_current_user
from models import Users

router = APIRouter(prefix="/users", tags=["users"])

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    user_model = db.query(Users).filter(Users.id == user.id).first()

    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user_model.id != user.get("id"):
        raise HTTPException(status_code=401, detail="User not authorised")

    return user
