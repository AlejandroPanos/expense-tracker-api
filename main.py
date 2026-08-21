# Imports
from fastapi import FastAPI
from database import engine
import models
from routers import auth, users, categories, expenses, budgets

# Create the app
app = FastAPI()

# Create the engine
models.Base.metadata.create_all(bind=engine)

# Use all the routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(budgets.router)
