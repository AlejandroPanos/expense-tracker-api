from routers.budgets import get_db
from routers.auth import get_current_user
from .utils import *
from models import Budget
from fastapi import status

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_create_budget(test_category):
    """
    Verify POST /budgets/ creates a budget for a category the user owns.

    Args:
        test_category: Fixture that inserts a real Category row, owned by
            the test user, before the test runs.

    Asserts:
        - Response status is 201 Created.
        - The returned budget has the correct monthly_limit and category_id.
    """
    response = client.post(
        "/budgets/",
        json={"category_id": test_category.id, "monthly_limit": 500},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["monthly_limit"] == 500
    assert response.json()["category_id"] == test_category.id


def test_create_budget_invalid_category():
    """
    Verify POST /budgets/ rejects a category_id that doesn't exist or
    doesn't belong to the current user.

    Asserts:
        - Response status is 404 Not Found.
        - The error detail explains the category is missing or not owned.
    """
    response = client.post(
        "/budgets/",
        json={"category_id": 999, "monthly_limit": 500},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Category not found or does not belong to user"


def test_get_budget_list(test_budget):
    """
    Verify GET /budgets/ returns the current user's budgets.

    Args:
        test_budget: Fixture that inserts a real Budget row (and its
            dependent user/category) before the test runs.

    Asserts:
        - Response status is 200 OK.
        - Exactly one budget is returned, matching test_budget's id.
    """
    response = client.get("/budgets/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == test_budget.id


def test_update_budget(test_budget):
    """
    Verify PUT /budgets/{budget_id} updates an existing budget's monthly limit.

    Args:
        test_budget: Fixture that inserts a real Budget row before the test runs.

    Asserts:
        - Response status is 200 OK.
        - The returned monthly_limit reflects the new value.
    """
    response = client.put(
        f"/budgets/{test_budget.id}",
        json={"monthly_limit": 750},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["monthly_limit"] == 750


def test_update_budget_not_found():
    """
    Verify PUT /budgets/{budget_id} returns 404 for a budget ID that
    doesn't exist.

    Asserts:
        - Response status is 404 Not Found.
        - The error detail confirms the budget was not found.
    """
    response = client.put(
        "/budgets/999",
        json={"monthly_limit": 750},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Budget not found"


def test_delete_budget(test_budget):
    """
    Verify DELETE /budgets/{budget_id} removes the budget from the database.

    Args:
        test_budget: Fixture that inserts a real Budget row before the test runs.

    Asserts:
        - Response status is 200 OK with a success message.
        - The budget row no longer exists in the database after deletion.
    """
    response = client.delete(f"/budgets/{test_budget.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Budget deleted correctly"

    db = TestingSessionLocal()
    deleted = db.query(Budget).filter(Budget.id == test_budget.id).first()
    assert deleted is None


def test_delete_budget_not_found():
    response = client.delete("/budgets/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Budget not found"


def test_get_budget_status_by_category(test_expense, test_budget, test_category):
    response = client.get(f"/budgets/{test_category.id}/status")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["category"] == test_category.name
    assert response.json()["monthly_limit"] == test_budget.monthly_limit
    assert response.json()["spent"] == test_expense.amount
    assert (
        response.json()["remaining"] == test_budget.monthly_limit - test_expense.amount
    )


def test_get_budget_status_no_budget_set(test_category):
    response = client.get(f"/budgets/{test_category.id}/status")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "No budget set for this category"


def test_get_budget_status_no_expenses(test_budget, test_category):
    response = client.get(f"/budgets/{test_category.id}/status")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["spent"] == 0.0
    assert response.json()["remaining"] == test_budget.monthly_limit
