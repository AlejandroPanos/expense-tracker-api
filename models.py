from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class User(Base):
    __tablename__ = "users"


class Category(Base):
    __tablename__ = "categories"


class Expense(Base):
    __tablename__ = "expenses"


class Budget(Base):
    __tablename__ = "budgets"
