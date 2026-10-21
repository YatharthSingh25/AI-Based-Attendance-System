"""Tests for the AI Attendance System FastAPI backend.

Uses an isolated SQLite database by default; set TEST_DATABASE_URL to run
against a dedicated PostgreSQL test database. For PostgreSQL, every run uses a
unique schema, so existing schemas and data are never dropped or modified.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from app.core.auth import auth_service
from app.database import get_db, normalize_database_url
from app.main import app, get_current_user
from app.models import Attendance, Base, User

# Isolated test database - never points at production data.
# Override with TEST_DATABASE_URL to run against a dedicated Postgres test DB.
SQLALCHEMY_DATABASE_URL = normalize_database_url(
    os.getenv("TEST_DATABASE_URL") or "sqlite:///./test_attendance.db"
)

_engine_kwargs = {}
TEST_SCHEMA = None
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    _engine_kwargs["poolclass"] = StaticPool
elif SQLALCHEMY_DATABASE_URL.startswith(
    ("postgresql://", "postgresql+psycopg2://")
):
    TEST_SCHEMA = f"attendance_backend_test_{uuid.uuid4().hex[:12]}"
    _engine_kwargs["connect_args"] = {"options": f"-csearch_path={TEST_SCHEMA}"}
else:
    raise RuntimeError(
        "TEST_DATABASE_URL must use SQLite or PostgreSQL. Refusing to run "
        "tests that could drop tables in an unsupported database."
    )

engine = create_engine(SQLALCHEMY_DATABASE_URL, **_engine_kwargs)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def test_db():
    """Create the schema in the isolated test database."""
    if TEST_SCHEMA:
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{TEST_SCHEMA}"'))
    try:
        Base.metadata.create_all(bind=engine)
        yield
    finally:
        if TEST_SCHEMA:
            with engine.begin() as conn:
                conn.execute(text("SET search_path TO pg_catalog"))
                conn.execute(text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))
        else:
            Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def db_session(test_db):
    """Provide a session bound to the isolated test database."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def client(db_session):
    """Create a TestClient backed by the isolated test database."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    test_user = User(
        email="admin@test.local",
        password_hash="not-used-in-tests",
        role="ADMIN",
        name="Test Admin",
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(db_session):
    """TestClient using the real JWT dependency (no current-user override)."""
    saved_overrides = dict(app.dependency_overrides)
    app.dependency_overrides.clear()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved_overrides)


def _role_headers(db_session, role: str):
    """Create a user with the given role and return a real bearer-token header."""
    email = f"rbac-{role.lower()}-{uuid.uuid4().hex}@test.local"
    user = User(
        email=email,
        password_hash=auth_service.hash_password("Secret123!"),
        role=role,
        name=f"{role.title()} User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = auth_service.create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _student_payload():
    suffix = uuid.uuid4().hex[:6]
    return {
        "student_id": f"RBA{int(suffix, 16) % 1000:03d}",
        "name": "RBAC Student",
        "email": f"student-{suffix}@college.edu",
        "course": "CSE",
        "branch": "CSE",
        "section": "A",
        "semester": 4,
    }


class TestHealthEndpoint:
    """Test the /health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AI Attendance System API"
        assert "version" in data

    def test_does_not_expose_secrets(self, client):
        """Health endpoint should not expose database credentials or JWT secrets."""
        response = client.get("/health")
        body = str(response.json()).lower()
        assert "postgres" not in body  # no DB URLs in response
        assert "secret" not in body


class TestAuthRoutes:
    """Test authentication endpoints."""

    def test_login_with_valid_credentials(self, client):
        """Login with a user that doesn't exist should fail gracefully."""
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent@test.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_with_invalid_payload(self, client):
        """Login with missing fields should fail."""
        response = client.post("/api/auth/login", data={})
        assert response.status_code == 422  # Validation error


class TestLoginFlow:
    """Registration + login using the real JWT dependency."""

    def test_register_login_and_use_token(self, auth_client):
        email = "authflow@college.edu"
        password = "Secret123!"

        register = auth_client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "name": "Auth Flow", "role": "ADMIN"},
        )
        assert register.status_code == 200, register.text
        assert register.json()["user"]["role"] == "STUDENT"

        # OAuth2PasswordRequestForm: form-encoded username/password (email as username)
        login = auth_client.post(
            "/api/auth/login",
            data={"username": email, "password": password},
        )
        assert login.status_code == 200, login.text
        body = login.json()
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == email
        token = body["access_token"]
        assert token

        # The issued token is accepted, but public registration creates a
        # STUDENT, which is not allowed to list students (403, not 401).
        protected = auth_client.get(
            "/api/students",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert protected.status_code == 403, protected.text
        assert protected.json()["detail"] == "Insufficient permissions"

    def test_login_rejects_wrong_password(self, auth_client):
        response = auth_client.post(
            "/api/auth/login",
            data={"username": "authflow@college.edu", "password": "wrong-password"},
        )
        assert response.status_code == 401


class TestRegistrationSecurity:
    """Public registration must never grant administrator access."""

    @pytest.mark.parametrize("requested_role", ["ADMIN", "SUPERADMIN", "ROOT"])
    def test_privileged_registration_is_forced_to_student(
        self, auth_client, requested_role
    ):
        email = f"public-{requested_role.lower()}@college.edu"
        password = "Secret123!"

        response = auth_client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
                "name": "Public User",
                "role": requested_role,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["user"]["role"] == "STUDENT"

        login = auth_client.post(
            "/api/auth/login",
            data={"username": email, "password": password},
        )
        assert login.status_code == 200, login.text
        assert login.json()["user"]["role"] == "STUDENT"

    def test_faculty_registration_is_preserved(self, auth_client):
        email = "public-faculty@college.edu"
        password = "Secret123!"

        response = auth_client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
                "name": "Public Faculty",
                "role": "FACULTY",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["user"]["role"] == "FACULTY"

        login = auth_client.post(
            "/api/auth/login",
            data={"username": email, "password": password},
        )
        assert login.status_code == 200, login.text
        assert login.json()["user"]["role"] == "FACULTY"

    def test_registration_defaults_to_student(self, auth_client):
        email = "public-default@college.edu"
        password = "Secret123!"

        response = auth_client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "name": "Default Role"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["user"]["role"] == "STUDENT"

    def test_admin_seed_creates_admin_idempotently(self, db_session):
        from app.seed_admin import seed_admin

        email = "seed-admin@college.edu"
        user, created = seed_admin(
            email, "StrongPass123!", "Seed Admin", db=db_session
        )
        assert created is True
        assert user.role == "ADMIN"

        again, created_again = seed_admin(
            email, "StrongPass123!", "Seed Admin", db=db_session
        )
        assert created_again is False
        assert again.id == user.id
        assert again.role == "ADMIN"

    def test_admin_seed_does_not_promote_existing_student(self, db_session):
        from app.seed_admin import seed_admin

        email = "seed-student@college.edu"
        student = User(email=email, password_hash="not-used", role="STUDENT")
        db_session.add(student)
        db_session.commit()

        with pytest.raises(RuntimeError):
            seed_admin(email, "StrongPass123!", db=db_session)

        db_session.refresh(student)
        assert student.role == "STUDENT"


class TestStudentCRUD:
    """Test student creation, retrieval, updating, and deletion."""

    def test_create_student(self, client):
        """Test creating a new student via API."""
        student_data = {
            "student_id": "CSE001",
            "name": "Test Student",
            "email": "test@college.edu",
            "course": "Data Structures",
            "branch": "CSE",
            "section": "A",
            "semester": 3,
        }
        response = client.post("/api/students", json=student_data)
        assert response.status_code == 200
        data = response.json()["student"]
        assert data["student_id"] == "CSE001"
        assert data["name"] == "Test Student"
        assert data["email"] == "test@college.edu"

    def test_create_student_duplicate_id(self, client):
        """Test that creating a student with duplicate student_id fails."""
        # First create
        student_data = {
            "student_id": "CSE001",
            "name": "Test Student",
            "email": "test@college.edu",
            "course": "Data Structures",
            "branch": "CSE",
            "section": "A",
            "semester": 3,
        }
        client.post("/api/students", json=student_data)
        # Second create with same student_id should fail
        response = client.post("/api/students", json=student_data)
        assert response.status_code == 400  # Bad request
        assert "already exists" in response.json()["detail"].lower()

    def test_get_students(self, client):
        """Test retrieving all students."""
        response = client.get("/api/students")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_student_by_id(self, client):
        """Test retrieving a specific student by ID."""
        # First create a student
        student_data = {
            "student_id": "CSE002",
            "name": "Test Student 2",
            "email": "test2@college.edu",
            "course": "Database Management",
            "branch": "CSE",
            "section": "B",
            "semester": 4,
        }
        create_resp = client.post("/api/students", json=student_data)
        assert create_resp.status_code == 200
        student_id = str(create_resp.json()["student"]["id"])

        # Now retrieve
        response = client.get(f"/api/students/{student_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == "CSE002"

    def test_update_student(self, client):
        """Test updating student information."""
        student_data = {
            "student_id": "CSE003",
            "name": "Test Student 3",
            "email": "test3@college.edu",
            "course": "Operating Systems",
            "branch": "IT",
            "section": "C",
            "semester": 2,
        }
        create_resp = client.post("/api/students", json=student_data)
        assert create_resp.status_code == 200
        student_id = str(create_resp.json()["student"]["id"])

        # Update the student
        update_data = {"name": "Updated Name", "email": "updated@college.edu"}
        response = client.put(f"/api/students/{student_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()["student"]
        assert data["name"] == "Updated Name"

    def test_delete_student(self, client):
        """Test deleting a student."""
        student_data = {
            "student_id": "CSE004",
            "name": "Test Student 4",
            "email": "test4@college.edu",
            "course": "Computer Networks",
            "branch": "EEE",
            "section": "A",
            "semester": 3,
        }
        create_resp = client.post("/api/students", json=student_data)
        assert create_resp.status_code == 200
        student_id = str(create_resp.json()["student"]["id"])

        # Delete the student
        response = client.delete(f"/api/students/{student_id}")
        assert response.status_code == 200

        # Verify it's gone
        get_response = client.get(f"/api/students/{student_id}")
        assert get_response.status_code == 404  # Not found


class TestAttendanceDuplicatePrevention:
    """Test that duplicate attendance cannot be recorded."""

    def test_cannot_mark_duplicate_attendance(self, client, db_session):
        """Duplicate attendance is prevented by the UNIQUE(student_id, session_id) constraint."""
        # Create a student
        student_data = {
            "student_id": "CSE005",
            "name": "Duplicate Tester",
            "email": "dup@test.edu",
            "course": "Data Structures",
            "branch": "CSE",
            "section": "A",
            "semester": 3,
        }
        create_resp = client.post("/api/students", json=student_data)
        assert create_resp.status_code == 200
        student_id = int(create_resp.json()["student"]["id"])

        # Create an attendance session
        session_data = {"subject": "Data Structures", "section": "A"}
        session_resp = client.post("/api/attendance/sessions", json=session_data)
        assert session_resp.status_code == 200
        session_id = session_resp.json()["session"]["id"]

        # Mark student as present first time
        db_session.add(
            Attendance(
                student_id=student_id,
                session_id=session_id,
                status="present",
                method="photo",
            )
        )
        db_session.commit()

        # Try to mark the same student again for the same session
        db_session.add(
            Attendance(
                student_id=student_id,
                session_id=session_id,
                status="present",
                method="photo",
            )
        )
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestAttendanceCreation:
    """Test attendance record persistence and retrieval."""

    def test_create_attendance_record(self, client, db_session):
        """Test that a persisted attendance record is retrievable for its session."""
        # Create a student
        student_data = {
            "student_id": "CSE006",
            "name": "Attendance Test",
            "email": "attend@test.edu",
            "course": "Computer Networks",
            "branch": "CSE",
            "section": "A",
            "semester": 3,
        }
        create_resp = client.post("/api/students", json=student_data)
        assert create_resp.status_code == 200
        student_id = int(create_resp.json()["student"]["id"])

        # Create an attendance session
        session_data = {"subject": "Computer Networks", "section": "A"}
        session_resp = client.post("/api/attendance/sessions", json=session_data)
        assert session_resp.status_code == 200
        session_id = session_resp.json()["session"]["id"]

        # Persist an attendance record (as produced by photo/live processing)
        record = Attendance(
            student_id=student_id,
            session_id=session_id,
            status="present",
            confidence=95.0,
            method="photo",
            verified=True,
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        assert record.id is not None

        # The record is returned by the session attendance endpoint
        response = client.get(f"/api/attendance/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert any(str(a["student_id"]) == str(student_id) for a in data)
        assert any(a["status"] == "present" for a in data)


class TestAPIValidation:
    """Test API request validation."""

    def test_invalid_student_creation_missing_fields(self, client):
        """Test that creating a student with missing required fields fails validation."""
        response = client.post("/api/students", json={"student_id": "CSE001"})
        assert response.status_code == 422  # Validation error

    def test_invalid_attendance_session(self, client):
        """Test creating attendance session with missing fields."""
        response = client.post("/api/attendance/sessions", json={})
        assert response.status_code == 422  # Validation error


class TestCORSMiddleware:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.options(
            "/api/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or "access-control-allow-methods" in response.headers


def test_app_imports_and_routes():
    """Verify the FastAPI app imports correctly and has expected routes."""
    from app.main import app as fastapi_app

    # Verify app is initialized
    assert fastapi_app is not None
    assert hasattr(fastapi_app, "routes")

    # Check for expected route paths
    route_paths = [route.path for route in fastapi_app.routes]
    expected_paths = ["/health", "/api"]

    for path in expected_paths:
        # At least check the app has some routes
        matching = [r for r in route_paths if path in r]
        assert len(matching) > 0, f"Expected to find routes matching '{path}'"


class TestRoleAuthorization:
    """Server-side role checks for protected API routes."""

    def test_unauthenticated_requests_return_401(self, auth_client):
        for path in (
            "/api/students",
            "/api/students/1",
            "/api/attendance/sessions",
            "/api/analytics/overview",
            "/api/analytics/student/1",
            "/api/settings/thresholds",
            "/api/ml/predictions",
        ):
            response = auth_client.get(path)
            assert response.status_code == 401, (path, response.text)

        response = auth_client.post("/api/students", json=_student_payload())
        assert response.status_code == 401, response.text

    def test_student_forbidden_from_staff_routes(self, auth_client, db_session):
        headers = _role_headers(db_session, "STUDENT")

        for path in (
            "/api/students",
            "/api/students/1",
            "/api/attendance/sessions",
            "/api/attendance/session_1",
            "/api/analytics/overview",
            "/api/analytics/student/1",
            "/api/ml/predictions",
            "/api/settings/thresholds",
            "/api/settings/liveness",
            "/api/settings/ml",
        ):
            response = auth_client.get(path, headers=headers)
            assert response.status_code == 403, (path, response.text)
            assert response.json()["detail"] == "Insufficient permissions"

    def test_student_cannot_perform_staff_or_admin_actions(self, auth_client, db_session):
        headers = _role_headers(db_session, "STUDENT")

        requests = (
            ("post", "/api/students", {"json": _student_payload()}),
            (
                "post",
                "/api/attendance/sessions",
                {"json": {"subject": "Data Structures", "section": "A"}},
            ),
            (
                "post",
                "/api/settings/thresholds",
                {"json": {"highConfidence": 95, "reviewThreshold": 80, "unknownThreshold": 70}},
            ),
            ("post", "/api/settings/liveness", {"json": {"enabled": False}}),
            ("post", "/api/settings/ml", {"json": {"model": "random_forest"}}),
            ("post", "/api/ml/train", {}),
            ("post", "/api/reports/export", {"json": {"format": "CSV"}}),
        )

        for method, path, kwargs in requests:
            response = getattr(auth_client, method)(path, headers=headers, **kwargs)
            assert response.status_code == 403, (path, response.text)

    def test_student_cannot_retrieve_records_by_id(self, auth_client, db_session):
        headers = _role_headers(db_session, "STUDENT")

        for path in (
            "/api/students/1",
            "/api/students/999999",
            "/api/analytics/student/1",
            "/api/attendance/session_1",
        ):
            response = auth_client.get(path, headers=headers)
            assert response.status_code == 403, (path, response.text)

    def test_faculty_can_access_permitted_routes(self, auth_client, db_session):
        headers = _role_headers(db_session, "FACULTY")
        student_data = _student_payload()

        create_student = auth_client.post(
            "/api/students", json=student_data, headers=headers
        )
        assert create_student.status_code == 200, create_student.text
        student_id = create_student.json()["student"]["id"]

        get_student = auth_client.get(f"/api/students/{student_id}", headers=headers)
        assert get_student.status_code == 200, get_student.text

        list_students = auth_client.get("/api/students", headers=headers)
        assert list_students.status_code == 200, list_students.text

        create_session = auth_client.post(
            "/api/attendance/sessions",
            json={"subject": "Data Structures", "section": "A"},
            headers=headers,
        )
        assert create_session.status_code == 200, create_session.text
        session_id = create_session.json()["session"]["id"]

        for path in (
            "/api/attendance/sessions",
            f"/api/attendance/{session_id}",
            "/api/analytics/overview",
            f"/api/analytics/student/{student_id}",
            "/api/settings/thresholds",
        ):
            response = auth_client.get(path, headers=headers)
            assert response.status_code == 200, (path, response.text)

        export = auth_client.post(
            "/api/reports/export", json={"format": "CSV"}, headers=headers
        )
        assert export.status_code == 200, export.text

        # Settings writes and ML training remain admin-only.
        update = auth_client.post(
            "/api/settings/thresholds",
            json={"highConfidence": 95, "reviewThreshold": 80, "unknownThreshold": 70},
            headers=headers,
        )
        assert update.status_code == 403, update.text

        train = auth_client.post("/api/ml/train", headers=headers)
        assert train.status_code == 403, train.text

    def test_admin_can_access_admin_routes(self, auth_client, db_session):
        headers = _role_headers(db_session, "ADMIN")

        for path in (
            "/api/settings/thresholds",
            "/api/settings/liveness",
            "/api/settings/ml",
            "/api/students",
        ):
            response = auth_client.get(path, headers=headers)
            assert response.status_code == 200, (path, response.text)

        updates = (
            (
                "/api/settings/thresholds",
                {"highConfidence": 95, "reviewThreshold": 80, "unknownThreshold": 70},
            ),
            (
                "/api/settings/liveness",
                {"enabled": False, "spoofThreshold": 0.6},
            ),
            (
                "/api/settings/ml",
                {"model": "random_forest", "autoTrain": False},
            ),
        )
        for path, payload in updates:
            response = auth_client.post(path, json=payload, headers=headers)
            assert response.status_code == 200, (path, response.text)


class TestMLEndpoints:
    """Contract and honesty checks for the ML routes."""

    def test_ml_service_imports_under_app_package(self):
        from app.services.ml.service import MLServices

        assert MLServices.training_available() is False

    @pytest.mark.parametrize("role", ["FACULTY", "ADMIN"])
    def test_authorized_predictions_return_list(
        self, auth_client, db_session, role
    ):
        headers = _role_headers(db_session, role)
        response = auth_client.get("/api/ml/predictions", headers=headers)

        assert response.status_code == 200, response.text
        assert isinstance(response.json(), list)

    def test_training_remains_admin_only(self, auth_client, db_session):
        for role in ("STUDENT", "FACULTY"):
            response = auth_client.post(
                "/api/ml/train", headers=_role_headers(db_session, role)
            )
            assert response.status_code == 403, (role, response.text)

        response = auth_client.post(
            "/api/ml/train", headers=_role_headers(db_session, "ADMIN")
        )
        assert response.status_code == 501, response.text

        body = response.json()
        assert body["status"] == "not_implemented"
        assert body["training_performed"] is False
        assert body["accuracy"] == 0
        assert body["model_type"] is None
        assert body["service_available"] is False
        assert "trained successfully" not in body["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])