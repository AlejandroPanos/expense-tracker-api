from routers.users import get_current_user, get_db
from .utils import *
from models import Users
from fastapi import status

# Swap out the real DB session and real JWT-auth for the test ones during tests,
# so requests never touch the production database.
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_return_user(test_user):
    response = client.get("/users/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == "alex@gmail.com"
    assert response.json()["username"] == "alex"
    assert response.json()["first_name"] == "alex"
    assert response.json()["last_name"] == "panos"
    assert response.json()["role"] == "admin"
    assert response.json()["phone_number"] == "+34600600600"


def test_update_password(test_user):
    response = client.put(
        "/users/update_password",
        json={"current_password": "123456", "new_password": "alextest12"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_update_phone(test_user):
    response = client.put("/users/phone_number", json={"phone": "+34606606606"})
    assert response.status_code == status.HTTP_204_NO_CONTENT
