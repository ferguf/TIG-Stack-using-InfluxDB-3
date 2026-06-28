"""File Name: 'db_setup.py' and version '1.0.0' date: 'November 29, 2025 4:48 PM MST' (Initial SQLAlchemy configuration file for engine and SessionLocal.)"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from db_config import get_sqlalchemy_url

# Use the helper function to construct the SQLAlchemy compatible URL
SQLALCHEMY_DATABASE_URL = get_sqlalchemy_url()

# --- 1. Create the SQLAlchemy Engine ---
# The engine manages the connection to the database.
try:
    # pool_pre_ping=True checks the health of the connection pool before use.
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True
    )
    print("✅ SQLAlchemy Engine configured successfully.")
except Exception as e:
    print(f"❌ SQLAlchemy Engine creation failed using URL: {SQLALCHEMY_DATABASE_URL}")
    print(f"   Error details: {e}")
    # Setting engine to None will prevent SessionLocal creation from crashing
    engine = None 

# --- 2. Create the SessionLocal class ---
SessionLocal = None
if engine:
    try:
        # Configure sessionmaker: 
        # autocommit=False: Transactions must be explicitly committed/rolled back.
        # autoflush=False: Prevents flush operations before query executions.
        # bind=engine: Binds the session to the created engine.
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("✅ SQLAlchemy SessionLocal created successfully.")
    except Exception as e:
        print(f"❌ SQLAlchemy SessionLocal creation failed: {e}")
        SessionLocal = None


# --- 3. Base Class for ORM Models ---
# All ORM models (tables) will inherit from this Base class.
Base = declarative_base()


# Dependency to get a DB session (used in FastAPI/other applications)
def get_db():
    """Provides a transactional database session."""
    db = None
    if SessionLocal:
        try:
            db = SessionLocal()
            yield db
        finally:
            if db:
                db.close()
    else:
        # If engine or SessionLocal failed to initialize, yield an error state
        print("⚠️ Attempted to get database session, but SessionLocal is not initialized.")
        # In a production setup, this would raise an HTTP 500 or similar
        # For this context, we just skip yielding a session
        yield None