from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from scripts.db_config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)

# Add expire_on_commit=False here
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False, 
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()