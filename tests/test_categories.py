from routers.categories import get_db
from routers.auth import get_current_user
from .utils import *
from models import Category
from fastapi import status

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_return_categories(test_category):
    response = client.get("/categories/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["name"] == "food"
