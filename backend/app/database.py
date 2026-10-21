from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from typing import Optional

Base = declarative_base()

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/attendance_ai"
PRODUCTION_ENVIRONMENTS = frozenset({"production", "prod"})


def _get_environment(environment: Optional[str] = None) -> str:
    return (
        environment
        or os.getenv("ENVIRONMENT")
        or os.getenv("APP_ENV")
        or "development"
    ).strip().lower()


def normalize_database_url(url: str) -> str:
    """Accept Render's legacy postgres:// prefix as SQLAlchemy's postgresql://."""
    url = (url or "").strip()
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def validate_database_config(
    database_url: Optional[str] = None,
    environment: Optional[str] = None,
) -> str:
    """Validate and normalize the configured database URL.

    Development may fall back to the local PostgreSQL default. Production must
    explicitly configure a PostgreSQL URL; SQLite and the local default are
    rejected so a misconfigured deployment fails before serving requests.
    """
    env = _get_environment(environment)
    raw_url = database_url if database_url is not None else os.getenv("DATABASE_URL")
    raw_url = (raw_url or "").strip()

    if not raw_url:
        if env in PRODUCTION_ENVIRONMENTS:
            raise RuntimeError(
                "DATABASE_URL must be set when ENVIRONMENT=production. "
                "Use a PostgreSQL URL, e.g. "
                "postgresql://user:password@host:5432/dbname."
            )
        raw_url = DEFAULT_DATABASE_URL

    url = normalize_database_url(raw_url)

    if env in PRODUCTION_ENVIRONMENTS:
        if url.startswith("sqlite"):
            raise RuntimeError(
                "SQLite is not supported when ENVIRONMENT=production. "
                "Set DATABASE_URL to a PostgreSQL database."
            )
        if url == DEFAULT_DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is still the local development default. "
                "Set it to the production PostgreSQL database URL."
            )
        if not url.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise RuntimeError(
                "DATABASE_URL must use the postgresql:// scheme in production."
            )

    return url


DATABASE_URL = normalize_database_url(
    (os.getenv("DATABASE_URL") or "").strip() or DEFAULT_DATABASE_URL
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Yield a request-scoped session and always return it to the pool."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables():
    """Create missing tables; never drops or resets existing data.

    Importing app.models registers every model on its Base metadata before
    create_all runs. create_all is idempotent (checkfirst) and only adds
    missing tables. Production configuration is validated first.
    """
    validate_database_config()

    from app import models  # noqa: F401  (registers all model classes)

    models.Base.metadata.create_all(bind=engine)
