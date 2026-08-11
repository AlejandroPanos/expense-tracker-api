from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load all the env variables from the .env file
load_dotenv()

# Pull the DB URL
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

# The engine is the core object that manages the connection to the database. This
# is done by using the `create_engine` function.
# `check_same_thread`: `False` ensures that requests from different threads don't
# get blocked. It is a security safeguard, but in development, it is ok to use.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal is a class that gets instantiated and produces a new session object
# whenever it is called
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Creates a Base class for all of our ORM models
Base = declarative_base()
