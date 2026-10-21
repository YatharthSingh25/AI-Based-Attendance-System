"""Create the initial administrator from environment variables.

Usage (from the backend directory):

    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD='<strong-password>' \
        python -m app.seed_admin

This is the only supported way to provision an ADMIN account. Public
registration may create STUDENT or FACULTY accounts, but privileged/unknown
roles fall back to STUDENT. The password is never printed or logged. The
command is idempotent: if the admin already exists it exits 0.
"""

import os
import sys

from pydantic import ValidationError

from app.core.auth import auth_service
from app.database import SessionLocal, create_db_and_tables
from app.schemas import UserCreate

MIN_ADMIN_PASSWORD_LENGTH = 12


def seed_admin(email: str, password: str, name: str = None, db=None):
    """Create an ADMIN account, or return the existing one.

    Returns (user, created). Raises RuntimeError if the email already belongs
    to a non-admin account. Never includes the password in error messages.
    """
    if len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        raise ValueError(
            f"ADMIN_PASSWORD must be at least {MIN_ADMIN_PASSWORD_LENGTH} characters."
        )
    if len(password) > 128:
        raise ValueError("ADMIN_PASSWORD must be at most 128 characters.")

    user_create = UserCreate(email=email, password=password, name=name)

    owns_session = db is None
    if owns_session:
        create_db_and_tables()
        db = SessionLocal()

    try:
        existing = auth_service.get_by_email(user_create.email, db)
        if existing:
            if existing.role == "ADMIN":
                return existing, False
            raise RuntimeError(
                "A non-admin account already exists for ADMIN_EMAIL; "
                "choose a different email for the administrator."
            )
        user = auth_service.create(user_create, db, role="ADMIN")
        return user, True
    finally:
        if owns_session:
            db.close()


def main() -> int:
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    name = os.getenv("ADMIN_NAME")

    if not email or not password:
        print(
            "ADMIN_EMAIL and ADMIN_PASSWORD must be set. No account was created.",
            file=sys.stderr,
        )
        return 1

    try:
        user, created = seed_admin(email, password, name)
    except ValidationError as exc:
        fields = ", ".join(
            ".".join(str(part) for part in error.get("loc", ()))
            for error in exc.errors()
        )
        print(f"Admin seed failed validation for: {fields}", file=sys.stderr)
        return 1
    except (ValueError, RuntimeError) as exc:
        print(f"Admin seed failed: {exc}", file=sys.stderr)
        return 1

    status = "created" if created else "already exists"
    print(f"Admin account {status}: {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
