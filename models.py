from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
import enum


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.user)
    is_active = Column(Boolean, default=True)
    phone_number = Column(String, unique=True, nullable=False)


class Category(Base):
    __tablename__ = "categories"


class Expense(Base):
    __tablename__ = "expenses"


class Budget(Base):
    __tablename__ = "budgets"
