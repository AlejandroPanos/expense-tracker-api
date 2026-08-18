# Imports
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from routers.auth import get_current_user

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

# Endpoints
