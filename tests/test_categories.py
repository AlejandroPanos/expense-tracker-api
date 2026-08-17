from routers.users import get_current_user, get_db
from .utils import *
from models import Category
from fastapi import status

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
