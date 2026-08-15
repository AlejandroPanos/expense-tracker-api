from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from .auth import get_current_user
from models import Users

router = APIRouter(prefix="/users", tags=["users"])

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class PhoneUpdateRequest(BaseModel):
    phone: str = Field(pattern=r"^\+?[1-9]\d{7,14}$")


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

    user_model = db.query(Users).filter(Users.id == user.get("id")).first()

    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user_model.id != user.get("id"):
        raise HTTPException(status_code=401, detail="User not authorised")

    return user_model


@router.post("/update_password", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_password(
    db: db_dependency, user: user_dependency, password_request: PasswordUpdateRequest
):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    user_model = db.query(Users).filter(Users.id == user.get("id")).first()

    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user_model.id != user.get("id"):
        raise HTTPException(status_code=401, detail="User not authorised")

    if not bcrypt_context.verify(
        password_request.current_password, user_model.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Unauthorised user")

    if bcrypt_context.verify(password_request.new_password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail="New password must be different")

    user_model.hashed_password = password_request.new_password

    db.add(user_model)
    db.commit()


@router.post("/phone_number", status_code=status.HTTP_204_NO_CONTENT)
async def update_phone_number(
    db: db_dependency, user: user_dependency, phone_request: PhoneUpdateRequest
):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authorised")

    user_model = db.query(Users).filter(Users.id == user.get("id")).first()

    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user_model.id != user.get("id"):
        raise HTTPException(status_code=401, detail="User not authorised")

    user_model.phone_number = phone_request.phone

    db.add(user_model)
    db.commit()
