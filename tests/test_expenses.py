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
