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
    assert response.json()[0]["owner_id"] == test_category.owner_id


def test_create_category():
    response = client.post("/categories/", json={"name": "food"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "food"
    assert response.json()["owner_id"] == 1


def test_create_category_duplicate(test_category):
    response = client.post("/categories/", json={"name": "food"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Category already exists"


def test_get_category(test_category):
    response = client.get(f"/categories/{test_category.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "food"
    assert response.json()["owner_id"] == test_category.owner_id


def test_update_category(test_category):
    response = client.put(
        f"/categories/{test_category.id}",
        json={"new_name": "groceries"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "groceries"
    assert response.json()["id"] == test_category.id


def test_delete_category(test_category):
    response = client.delete(f"/categories/{test_category.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Category deleted successfully"

    db = TestingSessionLocal()
    deleted = db.query(Category).filter(Category.id == test_category.id).first()
    assert deleted is None
