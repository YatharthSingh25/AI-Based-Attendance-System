"""Database configuration validation tests."""

import pytest

from app.database import (
    DEFAULT_DATABASE_URL,
    normalize_database_url,
    validate_database_config,
)

ENV_VARS = ("ENVIRONMENT", "APP_ENV", "DATABASE_URL")


@pytest.fixture(autouse=True)
def clean_db_env(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_development_falls_back_to_local_postgres():
    assert validate_database_config(environment="development") == DEFAULT_DATABASE_URL


def test_development_allows_sqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./local.db")
    assert validate_database_config(environment="development") == "sqlite:///./local.db"


def test_production_requires_database_url():
    with pytest.raises(RuntimeError, match="DATABASE_URL must be set"):
        validate_database_config(environment="production")


def test_production_rejects_sqlite():
    with pytest.raises(RuntimeError, match="SQLite is not supported"):
        validate_database_config(
            database_url="sqlite:///./local.db", environment="production"
        )


def test_production_rejects_local_default():
    with pytest.raises(RuntimeError, match="local development default"):
        validate_database_config(
            database_url=DEFAULT_DATABASE_URL, environment="production"
        )


def test_production_rejects_non_postgres_scheme():
    with pytest.raises(RuntimeError, match="postgresql://"):
        validate_database_config(
            database_url="mysql://user:pass@host:3306/db", environment="production"
        )


def test_production_accepts_postgres_url():
    url = "postgresql://app:secret@db.internal:5432/attendance"
    assert validate_database_config(database_url=url, environment="production") == url


def test_legacy_postgres_prefix_is_normalized():
    url = "postgres://app:secret@db.internal:5432/attendance"
    expected = "postgresql://app:secret@db.internal:5432/attendance"
    assert normalize_database_url(url) == expected
    assert (
        validate_database_config(database_url=url, environment="production")
        == expected
    )
