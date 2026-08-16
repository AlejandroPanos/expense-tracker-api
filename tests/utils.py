import pytest
from main import app
from database import Base
from dotenv import load_dotenv
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from models import Users
from routers.auth import bcrypt_context

load_dotenv()

SQLALCHEMY_TEST_DATABASE_URL = os.getenv("SQLALCHEMY_TEST_DATABASE_URL")

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {"username": "alextest", "id": 1, "role": "admin"}


client = TestClient(app)


@pytest.fixture
def test_user():
    user = Users(
        email="alex@gmail.com",
        username="alex",
        first_name="alex",
        last_name="panos",
        hashed_password=bcrypt_context.hash("123456"),
        role="admin",
        is_active=True,
        phone_number="+34600600600",
    )

    db = TestingSessionLocal()
    db.add(user)
    db.commit()

    yield user
    with engine.connect() as connection:
        connection.execute(text("DELETE from users;"))
        connection.commit()
