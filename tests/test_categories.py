from routers.categories import get_db
from routers.auth import get_current_user
from .utils import *
from models import Category
from fastapi import status

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_return_categories(test_category):
    """
    Verify GET /categories/ returns the current user's categories.

    Args:
        test_category: Fixture that inserts a real Category row ("food"),
            owned by the test user, before the test runs.

    Asserts:
        - Response status is 200 OK.
        - The first (and only) category returned has the expected name
          and owner_id.
    """
    response = client.get("/categories/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["name"] == "food"
    assert response.json()[0]["owner_id"] == test_category.owner_id


def test_create_category():
    """
    Verify POST /categories/ creates a new category for the current user.

    Asserts:
        - Response status is 201 Created.
        - The returned category has the submitted name and the correct
          owner_id, derived from the authenticated user rather than the
          request body.
    """
    response = client.post("/categories/", json={"name": "food"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "food"
    assert response.json()["owner_id"] == 1


def test_create_category_duplicate(test_category):
    """
    Verify POST /categories/ rejects a category name that already exists
    for the current user.

    Args:
        test_category: Fixture that inserts a Category named "food" before
            the test runs, so this test's request collides with it.

    Asserts:
        - Response status is 400 Bad Request.
        - The error detail confirms the category already exists.
    """
    response = client.post("/categories/", json={"name": "food"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Category already exists"


def test_get_category(test_category):
    """
    Verify GET /categories/{category_id} returns a single category by ID.

    Args:
        test_category: Fixture that inserts a real Category row before
            the test runs.

    Asserts:
        - Response status is 200 OK.
        - The returned category's name and owner_id match test_category.
    """
    response = client.get(f"/categories/{test_category.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "food"
    assert response.json()["owner_id"] == test_category.owner_id


def test_update_category(test_category):
    """
    Verify PUT /categories/{category_id} renames an existing category.

    Args:
        test_category: Fixture that inserts a real Category row before
            the test runs.

    Asserts:
        - Response status is 200 OK.
        - The returned category reflects the new name, with the same id.
    """
    response = client.put(
        f"/categories/{test_category.id}",
        json={"new_name": "groceries"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "groceries"
    assert response.json()["id"] == test_category.id


def test_delete_category(test_category):
    """
    Verify DELETE /categories/{category_id} removes a category with no
    expenses or budgets attached to it.

    Args:
        test_category: Fixture that inserts a real Category row, with
            nothing else referencing it, before the test runs.

    Asserts:
        - Response status is 200 OK with a success message.
        - The category row no longer exists in the database after deletion.
    """
    response = client.delete(f"/categories/{test_category.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Category deleted successfully"

    db = TestingSessionLocal()
    deleted = db.query(Category).filter(Category.id == test_category.id).first()
    assert deleted is None
