""" File Name: 'cli_base.py' and version '1.0.0' date: '2025-11-30 17:10 MST' (Sets up SQLAlchemy Engine and Session factory.) """
# cli_base.py
"""
Common methods and utilities for database interaction.
Sets up the SQLAlchemy Engine and Session factory.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scripts.db_config import DATABASE_URL
import logging

# Configure basic logging
logging.basicConfig()
# Enable SQL logging (uncomment the line below to see generated SQL queries)
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# --- Database Initialization ---

def get_engine():
    """
    Creates and returns the SQLAlchemy Engine.
    The 'pool_pre_ping=True' ensures the connection is valid before use.
    """
    try:
        # echo=False means no SQL logging, set to True for debugging
        engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        return engine
    except Exception as e:
        print(f"Error creating database engine: {e}")
        return None

# The Engine instance
Engine = get_engine()

# The Session factory
if Engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)
else:
    # Define a dummy session if the engine failed to initialize
    SessionLocal = None
    print("WARNING: Database engine could not be initialized.")


# Dependency for getting a database session (common pattern)
def get_db():
    """
    Provides a managed database session instance.
    The 'with' statement ensures the session is closed automatically,
    even if errors occur.
    """
    if not SessionLocal:
        raise ConnectionError("Database connection not established.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()