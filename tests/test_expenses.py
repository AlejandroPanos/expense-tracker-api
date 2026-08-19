from routers.expenses import get_db
from routers.auth import get_current_user
from .utils import *
from models import Expense
from fastapi import status
from datetime import date

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_create_expense(test_expense, test_category):
    today_str = date.today().isoformat()

    response = client.post(
        "/expenses/",
        json={
            "amount": 500,
            "description": "An average description",
            "date": today_str,
            "category_id": test_category.id,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["amount"] == 500
    assert response.json()["description"] == "An average description"
    assert response.json()["date"] == today_str
    assert response.json()["category_id"] == test_category.id


def test_get_all_expenses(test_expense):
    response = client.get("/expenses/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_expenses_filtered_by_category(test_expense, test_category):
    response = client.get("/expenses/", params={"category_id": test_category.id})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["category_id"] == test_category.id


def test_get_expenses_filtered_by_amount_range(test_expense):
    response = client.get("/expenses/", params={"min_amount": 100, "max_amount": 1000})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
