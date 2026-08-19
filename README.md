# Expense Tracker API

A RESTful backend for tracking personal expenses, built with **FastAPI** and **SQLAlchemy**. Users can register, authenticate via JWT, organize spending into categories, log expenses, and set monthly budgets per category with real-time spend/remaining calculations.

This project was built as a practical exercise in designing a multi-table relational API with proper ownership-based authorization — every resource is scoped to the authenticated user, and cross-resource references (e.g. an expense's category) are validated server-side rather than trusted from client input.

## Features

- **Authentication** — user registration and JWT-based login (OAuth2 password flow)
- **Role-based access** — `user` and `admin` roles
- **Categories** — create, read, update, and delete personal spending categories
- **Expenses** — full CRUD, with filtering by category, date range, and amount range, plus pagination
- **Budgets** — monthly spending limits per category, with a status endpoint showing spend vs. remaining for the current month
- **Ownership enforcement** — every resource lookup is scoped to the authenticated user; a user can never read, modify, or delete another user's data, even by guessing an ID
- **Safe deletion** — deleting a category is blocked if expenses or budgets still reference it, preventing accidental data loss
- **Aggregation endpoints** — total spend grouped by category, and monthly budget status computed via SQL aggregation

## Tech Stack

| Layer      | Technology                                                                                                        |
| ---------- | ----------------------------------------------------------------------------------------------------------------- |
| Framework  | [FastAPI](https://fastapi.tiangolo.com/)                                                                          |
| ORM        | [SQLAlchemy](https://www.sqlalchemy.org/)                                                                         |
| Database   | SQLite (dev/test)                                                                                                 |
| Validation | [Pydantic](https://docs.pydantic.dev/)                                                                            |
| Auth       | JWT ([python-jose](https://github.com/mpdavis/python-jose)) + [passlib](https://passlib.readthedocs.io/) (bcrypt) |
| Testing    | [pytest](https://docs.pytest.org/) + [httpx](https://www.python-httpx.org/) TestClient                            |
| Server     | [Uvicorn](https://www.uvicorn.org/)                                                                               |

## Project Structure

```
expense_tracker/
├── main.py                  # App entrypoint, router registration, table creation
├── database.py               # Engine, session factory, declarative base
├── models.py                  # SQLAlchemy ORM models (Users, Category, Expense, Budget)
├── conftest.py                 # Enables absolute imports for pytest
├── requirements.txt
├── .env                          # SECRET_KEY, ALGORITHM, database URLs (not committed)
├── routers/
│   ├── auth.py                    # Registration, login, JWT helpers, get_current_user
│   ├── users.py                    # Profile, password/phone updates
│   ├── categories.py                # Category CRUD
│   ├── expenses.py                   # Expense CRUD, filtering, summary
│   └── budgets.py                     # Budget CRUD, per-category status
└── tests/
    ├── utils.py                       # Test DB setup, fixtures, dependency overrides
    ├── test_auth.py
    ├── test_users.py
    ├── test_categories.py
    ├── test_expenses.py
    └── test_budgets.py
```

## Data Model

```
Users (1) ──< Category (1) ──< Expense
  │                │
  │                └──< Budget
  ├──< Expense
  └──< Budget
```

- A **User** owns many Categories, Expenses, and Budgets.
- A **Category** belongs to one User and has many Expenses and Budgets.
- An **Expense** belongs to one User and one Category.
- A **Budget** sets a monthly limit for one Category, belonging to one User.

Deleting a Category is **blocked** if any Expense or Budget still references it — the API returns a `400` with a count of what's still attached, rather than silently cascading the deletion.

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
git clone <repo-url>
cd expense_tracker
python -m venv trackervenv
source trackervenv/bin/activate   # Windows: trackervenv\Scripts\activate
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the project root:

```dotenv
SQLALCHEMY_DATABASE_URL=sqlite:///./expenses.db
SQLALCHEMY_TEST_DATABASE_URL=sqlite:///./testdb.db
SECRET_KEY=<generate with the command below>
ALGORITHM=HS256
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Run the app

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`.

### Run the tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=routers --cov=models --cov-report=term-missing
```

## API Overview

All routes except registration and login require a `Bearer` JWT in the `Authorization` header, obtained from `/auth/token`.

### Auth — `/auth`

| Method | Path          | Description                        |
| ------ | ------------- | ---------------------------------- |
| POST   | `/auth`       | Register a new user                |
| POST   | `/auth/token` | Log in, returns a JWT access token |

### Users — `/users`

| Method | Path                     | Description                                 |
| ------ | ------------------------ | ------------------------------------------- |
| GET    | `/users/`                | Get the current user's profile              |
| PUT    | `/users/update_password` | Change password (requires current password) |
| PUT    | `/users/phone_number`    | Update phone number                         |

### Categories — `/categories`

| Method | Path                        | Description                                                  |
| ------ | --------------------------- | ------------------------------------------------------------ |
| POST   | `/categories/`              | Create a category                                            |
| GET    | `/categories/`              | List the current user's categories                           |
| GET    | `/categories/{category_id}` | Get a single category                                        |
| PUT    | `/categories/{category_id}` | Rename a category                                            |
| DELETE | `/categories/{category_id}` | Delete a category (blocked if expenses/budgets reference it) |

### Expenses — `/expenses`

| Method | Path                     | Description                                                                                                   |
| ------ | ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| POST   | `/expenses/`             | Log a new expense                                                                                             |
| GET    | `/expenses/`             | List expenses — supports `category_id`, `start_date`, `end_date`, `min_amount`, `max_amount`, `skip`, `limit` |
| GET    | `/expenses/summary`      | Total spend grouped by category                                                                               |
| GET    | `/expenses/{expense_id}` | Get a single expense                                                                                          |
| PUT    | `/expenses/{expense_id}` | Update an expense                                                                                             |
| DELETE | `/expenses/{expense_id}` | Delete an expense                                                                                             |

### Budgets — `/budgets`

| Method | Path                            | Description                                       |
| ------ | ------------------------------- | ------------------------------------------------- |
| POST   | `/budgets/`                     | Create a monthly budget for a category            |
| GET    | `/budgets/`                     | List the current user's budgets                   |
| PUT    | `/budgets/{budget_id}`          | Update a budget's monthly limit                   |
| DELETE | `/budgets/{budget_id}`          | Delete a budget                                   |
| GET    | `/budgets/{category_id}/status` | Spend vs. remaining for a category, current month |

## Security Notes

- Passwords are hashed with **bcrypt** and never stored or returned in plaintext.
- JWTs are short-lived (20 minutes) and signed with `HS256`.
- Every resource lookup by ID is scoped with an ownership check (`owner_id == current_user.id`) — a valid token alone is not sufficient to access another user's data.
- Cross-resource references (e.g. attaching an expense to a `category_id`) are validated server-side to confirm the referenced resource actually belongs to the requesting user, preventing IDOR-style access to other users' data.

## License

This project is for educational purposes.
