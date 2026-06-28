import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from core.config import DATABASE_URL

logger = logging.getLogger(__name__)

# --- Database Initialization ---
def get_engine():
    """
    Creates and returns the SQLAlchemy Engine.
    The 'pool_pre_ping=True' ensures the connection is valid before use.
    """
    try:
        engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)
        return engine
    except Exception as e:
        logger.error(f"Error creating database engine: {e}")
        return None

# The globally accessible Engine instance
Engine = get_engine()

# The Session factory
if Engine:
    SessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        expire_on_commit=False, 
        bind=Engine
    )
else:
    SessionLocal = None
    logger.warning("WARNING: Database engine could not be initialized.")

Base = declarative_base()

# --- Dependency Injections ---

def get_db():
    """
    FastAPI Dependency for getting a managed database session instance.
    The 'finally' block ensures the session is closed automatically.
    """
    if not SessionLocal:
        raise ConnectionError("Database connection not established.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session() -> Session:
    """
    Context manager for background tasks or internal scripts 
    that need a DB session outside of a FastAPI route.
    """
    if not SessionLocal:
        raise ConnectionError("Database connection not established.")
        
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()