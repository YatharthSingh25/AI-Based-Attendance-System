"""JWT configuration validation tests.

These exercise the configuration loader directly; the application singleton is
created at import time using the developer environment.
"""

import pytest

from app.core.auth import (
    DEV_JWT_SECRET,
    KNOWN_INSECURE_SECRETS,
    load_jwt_settings,
)

ENV_VARS = (
    "ENVIRONMENT",
    "APP_ENV",
    "JWT_SECRET",
    "JWT_ALGORITHM",
    "JWT_EXPIRES_MINUTES",
)


@pytest.fixture(autouse=True)
def clean_jwt_env(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_development_without_secret_uses_dev_default():
    settings = load_jwt_settings(environment="development")
    assert settings.secret_key == DEV_JWT_SECRET
    assert settings.algorithm == "HS256"
    assert settings.expires_minutes == 30


def test_production_requires_secret():
    with pytest.raises(RuntimeError, match="JWT_SECRET must be set"):
        load_jwt_settings(environment="production")


@pytest.mark.parametrize("insecure", sorted(KNOWN_INSECURE_SECRETS))
def test_production_rejects_known_insecure_secrets(monkeypatch, insecure):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", insecure)

    with pytest.raises(RuntimeError, match="known insecure default"):
        load_jwt_settings()


def test_production_rejects_short_secret(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "short-secret")

    with pytest.raises(RuntimeError, match="at least 32 characters"):
        load_jwt_settings()


def test_production_accepts_strong_secret(monkeypatch):
    strong = "s" * 48
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", strong)
    monkeypatch.setenv("JWT_ALGORITHM", "HS512")
    monkeypatch.setenv("JWT_EXPIRES_MINUTES", "60")

    settings = load_jwt_settings()
    assert settings.secret_key == strong
    assert settings.algorithm == "HS512"
    assert settings.expires_minutes == 60


def test_development_placeholder_secret_is_allowed(monkeypatch):
    placeholder = "change-this-to-a-secure-random-string"
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("JWT_SECRET", placeholder)

    settings = load_jwt_settings()
    assert settings.secret_key == placeholder


@pytest.mark.parametrize("algorithm", ["none", "RS256", "HS1", "MD5"])
def test_rejects_unsupported_algorithms(monkeypatch, algorithm):
    monkeypatch.setenv("JWT_ALGORITHM", algorithm)

    with pytest.raises(RuntimeError, match="Unsupported JWT_ALGORITHM"):
        load_jwt_settings(environment="development")


@pytest.mark.parametrize("value", ["not-a-number", "", "30.5"])
def test_rejects_non_integer_expiry(monkeypatch, value):
    monkeypatch.setenv("JWT_EXPIRES_MINUTES", value)

    with pytest.raises(RuntimeError, match="must be an integer"):
        load_jwt_settings(environment="development")


@pytest.mark.parametrize("value", ["0", "-5", "1441"])
def test_rejects_out_of_range_expiry(monkeypatch, value):
    monkeypatch.setenv("JWT_EXPIRES_MINUTES", value)

    with pytest.raises(RuntimeError, match="between 1 and 1440"):
        load_jwt_settings(environment="development")


def test_production_error_does_not_leak_secret(monkeypatch):
    secret = "short-secret-do-not-log"
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", secret)

    with pytest.raises(RuntimeError) as excinfo:
        load_jwt_settings()

    message = str(excinfo.value)
    assert secret not in message
