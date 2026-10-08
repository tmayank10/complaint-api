"""Database setup. SQLite so the project runs without a MySQL server.

The tables and relationships are the same shape you would use on MySQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_URL = "sqlite:///./complaints.db"

engine = create_engine(
    SQLALCHEMY_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
