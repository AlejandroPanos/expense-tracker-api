from routers.expenses import get_db
from routers.auth import get_current_user
from .utils import *
from models import Expense
from fastapi import status
from datetime import date

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_create_expense(test_expense, test_category):
    """
    Verify POST /expenses/ creates a new expense tied to a category the
    user owns.

    Args:
        test_expense: Fixture that inserts a real Expense (unused directly
            here, but ensures the surrounding user/category setup exists).
        test_category: Fixture that inserts a real Category, owned by the
            test user, to attach the new expense to.

    Asserts:
        - Response status is 201 Created.
        - The returned expense matches the submitted amount, description,
          date, and category_id.
    """
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
    """
    Verify GET /expenses/ returns the current user's expenses with no
    filters applied.

    Args:
        test_expense: Fixture that inserts a single real Expense row.

    Asserts:
        - Response status is 200 OK.
        - Exactly one expense is returned.
    """
    response = client.get("/expenses/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_expenses_filtered_by_category(test_expense, test_category):
    """
    Verify GET /expenses/?category_id=... correctly filters expenses by
    category.

    Args:
        test_expense: Fixture that inserts an Expense tied to test_category.
        test_category: Fixture that inserts the Category being filtered on.

    Asserts:
        - Response status is 200 OK.
        - The single matching expense is returned, with the expected
          category_id.
    """
    response = client.get("/expenses/", params={"category_id": test_category.id})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["category_id"] == test_category.id


def test_get_expenses_filtered_by_amount_range(test_expense):
    """
    Verify GET /expenses/?min_amount=...&max_amount=... includes an
    expense that falls within the given range.

    Args:
        test_expense: Fixture that inserts an Expense with amount=500,
            which falls inside the range used here.

    Asserts:
        - Response status is 200 OK.
        - The expense is included in the results.
    """
    response = client.get("/expenses/", params={"min_amount": 100, "max_amount": 1000})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_expenses_filtered_by_date_range(test_expense):
    """
    Verify GET /expenses/?start_date=...&end_date=... includes an expense
    dated within the given range.

    Args:
        test_expense: Fixture that inserts an Expense dated today, which
            falls inside the single-day range used here.

    Asserts:
        - Response status is 200 OK.
        - The expense is included in the results.
    """
    today_str = date.today().isoformat()
    response = client.get(
        "/expenses/", params={"start_date": today_str, "end_date": today_str}
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_expenses_filtered_by_amount_excludes_out_of_range(test_expense):
    """
    Verify GET /expenses/?min_amount=... correctly excludes an expense
    that falls below the threshold, proving the filter actually filters
    rather than just not breaking the query.

    Args:
        test_expense: Fixture that inserts an Expense with amount=500,
            which is below the min_amount=1000 used here.

    Asserts:
        - Response status is 200 OK.
        - No expenses are returned.
    """
    # test_expense has amount=500 — filtering for min_amount=1000 should exclude it
    response = client.get("/expenses/", params={"min_amount": 1000})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_expenses_filtered_by_date_excludes_out_of_range(test_expense):
    """
    Verify GET /expenses/?start_date=...&end_date=... correctly excludes
    an expense dated outside the given range.

    Args:
        test_expense: Fixture that inserts an Expense dated today, which
            falls outside the 2020 date range used here.

    Asserts:
        - Response status is 200 OK.
        - No expenses are returned.
    """
    response = client.get(
        "/expenses/",
        params={"start_date": "2020-01-01", "end_date": "2020-12-31"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_expenses_pagination(test_user, test_category):
    """
    Verify GET /expenses/?skip=...&limit=... correctly paginates results
    across multiple expenses.

    Args:
        test_user: Fixture providing the owner for the manually inserted
            expenses below.
        test_category: Fixture providing the category for the manually
            inserted expenses below.

    Asserts:
        - limit=2 returns exactly 2 of the 3 expenses created.
        - skip=2, limit=2 returns the remaining 1 expense.
    """
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
    """
    Verify GET /expenses/ never leaks another user's expenses, regardless
    of which filters are applied.

    Args:
        test_user: Fixture ensuring the authenticated test user (id=1) exists.
        test_category: Fixture ensuring the test user has at least one
            category, so there is data to contrast against the other user's.

    Asserts:
        - Response status is 200 OK.
        - None of the returned expenses belong to the manually created
          other_user, proving ownership scoping holds even though their
          data exists in the same database.
    """
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


def test_get_expenses_summary(test_expense, test_category):
    """
    Verify GET /expenses/summary correctly aggregates total spend grouped
    by category.

    Args:
        test_expense: Fixture that inserts an Expense tied to test_category.
        test_category: Fixture that inserts the Category the expense
            belongs to.

    Asserts:
        - Response status is 200 OK.
        - The response contains exactly one category entry, with
          total_spent equal to the single expense's amount.
    """
    response = client.get("/expenses/summary")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"category": test_category.name, "total_spent": test_expense.amount}
    ]


def test_get_expense_by_id(test_expense):
    """
    Verify GET /expenses/{expense_id} returns a single expense by ID.

    Args:
        test_expense: Fixture that inserts a real Expense row before the
            test runs.

    Asserts:
        - Response status is 200 OK.
        - The returned expense's id, amount, and description match
          test_expense.
    """
    response = client.get(f"/expenses/{test_expense.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == test_expense.id
    assert response.json()["amount"] == test_expense.amount
    assert response.json()["description"] == test_expense.description


def test_get_expense_by_id_not_found():
    """
    Verify GET /expenses/{expense_id} returns 404 for an expense ID that
    doesn't exist.

    Asserts:
        - Response status is 404 Not Found.
        - The error detail confirms the expense was not found.
    """
    response = client.get("/expenses/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Expense not found"


def test_get_expense_by_id_not_owner(test_expense):
    """
    Verify GET /expenses/{expense_id} refuses access to an expense that
    belongs to a different user, even with a valid ID.

    Args:
        test_expense: Fixture used only to ensure the surrounding
            user/category setup exists (not the target of this test).

    Asserts:
        - Response status is 401 Unauthorized when requesting an expense
          owned by a manually created other_user.
    """
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
        amount=250,
        description="Not yours",
        date=date.today(),
        owner_id=other_user.id,
        category_id=other_category.id,
    )
    db.add(other_expense)
    db.commit()
    db.refresh(other_expense)

    response = client.get(f"/expenses/{other_expense.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_expense_by_id(test_expense, test_category):
    new_date = date.today().isoformat()
    response = client.put(
        f"/expenses/{test_expense.id}",
        json={
            "amount": 750,
            "description": "Updated description",
            "date": new_date,
            "category_id": test_category.id,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["amount"] == 750
    assert response.json()["description"] == "Updated description"


def test_update_expense_by_id_not_found(test_category):
    response = client.put(
        "/expenses/999",
        json={
            "amount": 750,
            "description": "Updated description",
            "date": date.today().isoformat(),
            "category_id": test_category.id,
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Expense not found"


def test_update_expense_by_id_invalid_category(test_expense):
    response = client.put(
        f"/expenses/{test_expense.id}",
        json={
            "amount": 750,
            "description": "Updated description",
            "date": date.today().isoformat(),
            "category_id": 999,
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Category not found or does not belong to user"


def test_delete_expense(test_expense):
    response = client.delete(f"/expenses/{test_expense.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Expense deleted successfully"

    db = TestingSessionLocal()
    deleted = db.query(Expense).filter(Expense.id == test_expense.id).first()
    assert deleted is None


def test_delete_expense_not_found():
    response = client.delete("/expenses/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Expense not found"
