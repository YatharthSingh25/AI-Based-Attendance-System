"""PostgreSQL compatibility checks.

The DDL-compilation checks always run and do not need a server. The live test
is opt-in and uses a disposable, uniquely named schema so existing data is
never touched. Run it with:

    $env:TEST_POSTGRES_URL = "postgresql://user:pass@host:5432/test_db"
    .\\.venv\\Scripts\\python.exe -m pytest ..\\tests\\test_postgres_compat.py -v

The database user needs CREATE SCHEMA privileges. The schema is dropped at the
end of the test (or rolled back automatically on failure).
"""

import os
import uuid
from datetime import datetime

import pytest
from sqlalchemy import UniqueConstraint, create_engine, func, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

from app.database import normalize_database_url
from app.models import (
    Attendance,
    AttendanceSession,
    Base,
    Student,
    User,
)

EXPECTED_TABLES = {
    "attendance",
    "attendance_sessions",
    "audit_logs",
    "face_embeddings",
    "ml_predictions",
    "students",
    "timetable",
    "users",
}


def test_all_models_registered_before_ddl_compilation():
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_models_compile_with_postgresql_dialect():
    dialect = postgresql.dialect()
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect)).lstrip()
        assert ddl.startswith("CREATE TABLE")
        assert table.name in ddl
        assert "VARCHAR" in ddl or "INTEGER" in ddl


def test_unique_constraints_are_declared():
    assert User.__table__.c.email.unique
    assert Student.__table__.c.student_id.unique
    assert Student.__table__.c.email.unique
    assert AttendanceSession.__table__.c.session_id.unique

    unique = next(
        constraint
        for constraint in Attendance.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    )
    assert {column.name for column in unique.columns} == {
        "student_id",
        "session_id",
    }


def test_foreign_keys_resolve_against_models():
    assert {fk.target_fullname for fk in Attendance.__table__.foreign_keys} == {
        "students.id",
        "attendance_sessions.session_id",
    }
    assert {fk.target_fullname for fk in AttendanceSession.__table__.foreign_keys} == {
        "users.id",
    }


POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")
requires_postgres = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="TEST_POSTGRES_URL is not set; skipping live PostgreSQL verification",
)


@requires_postgres
def test_live_postgresql_schema_creation_and_constraints():
    url = normalize_database_url(POSTGRES_URL)
    engine = create_engine(url, pool_pre_ping=True)
    if engine.dialect.name != "postgresql":
        pytest.fail("TEST_POSTGRES_URL must point to a PostgreSQL database")

    schema = f"attendance_test_{uuid.uuid4().hex[:12]}"
    try:
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
            conn.execute(text(f'SET search_path TO "{schema}"'))
            assert conn.execute(text("SELECT current_schema()")).scalar_one() == schema
            Base.metadata.create_all(bind=conn)

            tables = {
                row[0]
                for row in conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = current_schema()"
                    )
                )
            }
            assert EXPECTED_TABLES.issubset(tables)

            with Session(bind=conn) as session:
                admin = User(
                    email="pg-admin@example.com",
                    password_hash="not-a-real-hash",
                    role="ADMIN",
                    name="PG Admin",
                )
                student = Student(
                    student_id="PG001",
                    name="PG Student",
                    email="pg-student@example.com",
                    course="Databases",
                    branch="CSE",
                    section="A",
                    semester=3,
                )
                session.add_all([admin, student])
                session.flush()

                attendance_session = AttendanceSession(
                    session_id="pg-session-001",
                    subject="Databases",
                    faculty_id=admin.id,
                    section="A",
                    date=datetime.utcnow().date(),
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                )
                session.add(attendance_session)
                session.flush()

                record = Attendance(
                    student_id=student.id,
                    session_id=attendance_session.session_id,
                    status="present",
                    confidence=98.5,
                    method="photo",
                    verified=True,
                )
                session.add(record)
                session.flush()

                assert record.student.email == "pg-student@example.com"
                assert attendance_session.faculty.email == "pg-admin@example.com"

                with pytest.raises(IntegrityError):
                    with session.begin_nested():
                        session.add(
                            Attendance(
                                student_id=student.id,
                                session_id=attendance_session.session_id,
                                status="present",
                                method="photo",
                            )
                        )
                        session.flush()

                count = session.scalar(
                    select(func.count()).select_from(Attendance)
                )
                assert count == 1

            assert conn.execute(text("SELECT current_schema()")).scalar_one() == schema
            conn.execute(text("SET search_path TO pg_catalog"))
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    finally:
        engine.dispose()
