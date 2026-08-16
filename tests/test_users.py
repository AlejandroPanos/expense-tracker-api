from routers.users import get_current_user, get_db
from .utils import *
from models import Users
from fastapi import status

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
