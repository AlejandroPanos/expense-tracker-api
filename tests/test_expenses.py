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


def test_get_expenses_filtered_by_date_range(test_expense):
    today_str = date.today().isoformat()
    response = client.get(
        "/expenses/", params={"start_date": today_str, "end_date": today_str}
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_expenses_filtered_by_amount_excludes_out_of_range(test_expense):
    # test_expense has amount=500 — filtering for min_amount=1000 should exclude it
    response = client.get("/expenses/", params={"min_amount": 1000})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_expenses_filtered_by_date_excludes_out_of_range(test_expense):
    response = client.get(
        "/expenses/",
        params={"start_date": "2020-01-01", "end_date": "2020-12-31"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_expenses_pagination(test_user, test_category):
    db = TestingSessionLocal()

    for i in range(3):
        db.add(
            Expense(
                amount=100 + i,
                description=f"Expense {i}",
                date=date.today(),
                owner_id=test_user.id,
                category_id=test_category.id,
            )
        )
    db.commit()

    response = client.get("/expenses/", params={"limit": 2})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2

    response = client.get("/expenses/", params={"skip": 2, "limit": 2})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_all_expenses_only_returns_own_expenses(test_user, test_category):
    other_user = Users(
        email="other@gmail.com",
        username="other",
        first_name="Other",
        last_name="User",
        hashed_password=bcrypt_context.hash("password123"),
        role="user",
        is_active=True,
        phone_number="+34600600601",
    )
    db = TestingSessionLocal()
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    other_category = Category(name="other food", owner_id=other_user.id)
    db.add(other_category)
    db.commit()
    db.refresh(other_category)

    other_expense = Expense(
        amount=999,
        description="Not yours",
        date=date.today(),
        owner_id=other_user.id,
        category_id=other_category.id,
    )
    db.add(other_expense)
    db.commit()

    response = client.get("/expenses/")
    assert response.status_code == status.HTTP_200_OK
    assert all(e["owner_id"] != other_user.id for e in response.json())
