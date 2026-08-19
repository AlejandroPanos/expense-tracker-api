from routers.expenses import get_db
from routers.auth import get_current_user
from .utils import *
from models import Expense
from fastapi import status

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
