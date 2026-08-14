from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from typing import Annotated
from models import Users
from pydantic import BaseModel
from passlib.context import CryptContext
from database import SessionLocal
from starlette import status
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

# Create router
router = APIRouter(prefix="/auth", tags=["auth"])

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# We create the context to tell our app which algorithm to use to encrypt the passwords
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This is a dependency that allows fastapi to figure the route where our JWT will be
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


# This is the Pydantic schema that is expected in the request body
class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    phone_number: str


# This is the response schema and it will contain the JWT token
class Token(BaseModel):
    access_token: str
    token_type: str


# Get the current session's db and get the dependency to pass onto each route that needs it
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


###############
### Helpers ###
###############
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()

    if not user:
        return False

    if not bcrypt_context.verify(password, user.hashed_password):
        return False

    return user


def create_access_token(username: str, id: int, role: str, expire_delta: timedelta):
    expire = datetime.now(timezone.utc) + expire_delta
    encode = {"sub": username, "id": id, "role": role, "exp": expire}
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        id: int = payload.get("id")
        role: str = payload.get("role")

        if username is None or id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
            )

        return {"username": username, "id": id, "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
        )


##############
### Routes ###
##############
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, user: CreateUserRequest):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User details are incomplete",
        )

    create_user_model = Users(
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=bcrypt_context.hash(user.password),
        role=user.role,
        is_active=True,
        phone_number=user.phone_number,
    )

    db.add(create_user_model)
    db.commit()

    return create_user_model
