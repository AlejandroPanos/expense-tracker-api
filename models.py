from database import Base
from sqlalchemy import Column, Integer, Float, Date, String, Boolean, ForeignKey, Enum
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlalchemy.orm import relationship
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
    phone_number = Column(PhoneNumber, unique=True, nullable=False)

    category = relationship("Category", back_populates="owner")
    expense = relationship("Expense", back_populates="owner")
    budget = relationship("Buget", back_populates="owner")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey=("user.id"))

    owner = relationship("User", back_populates="category")
    expense = relationship("Expense", back_populates="category")
    budget = relationship("Budget", back_populates="category")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    owner_id = Column(Integer, ForeignKey=("user.id"))
    category_id = Column(Integer, ForeignKey=("category.id"))

    owner = relationship("User", back_populates="expense")
    category = relationship("Category", back_populates="expense")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("user.id"))
    category_id = Column(Integer, ForeignKey=("category.id"))
    monthly_limit = Column(Integer, nullable=False)

    owner = relationship("User", back_populates="budget")
    category = relationship("Category", back_populates="budget")
