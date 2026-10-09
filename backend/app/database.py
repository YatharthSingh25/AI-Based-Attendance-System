from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/attendance_ai"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_pool_size=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

get_db = lambda: SessionLocal()

def create_db_and_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)