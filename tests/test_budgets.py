from routers.budgets import get_db
from routers.auth import get_current_user
from .utils import *
from models import Budget
from fastapi import status
from datetime import date

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
