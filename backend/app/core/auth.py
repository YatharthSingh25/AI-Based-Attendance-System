import bcrypt
import jwt
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import User
from app.schemas import UserCreate

DEV_JWT_SECRET = "attendance-ai-secret-key-2026"
KNOWN_INSECURE_SECRETS = frozenset({
    DEV_JWT_SECRET,
    "change-this-to-a-secure-random-string",
    "changeme",
    "change-me",
    "secret",
    "your-secret-key",
    "<replace-with-a-random-secret-at-least-32-characters>",
    "REPLACE_WITH_GENERATED_SECRET",
})
ALLOWED_ALGORITHMS = frozenset({"HS256", "HS384", "HS512"})
PRODUCTION_ENVIRONMENTS = frozenset({"production", "prod"})
MIN_PRODUCTION_SECRET_LENGTH = 32
MIN_TOKEN_MINUTES = 1
MAX_TOKEN_MINUTES = 24 * 60

SAFE_DEFAULT_ROLE = "STUDENT"
PUBLIC_REGISTRATION_ROLES = frozenset({"STUDENT", "FACULTY"})


def resolve_public_registration_role(requested_role: Optional[str]) -> str:
    """Map a client-supplied role to a safe public registration role.

    STUDENT and FACULTY are legitimate self-registration roles. Privileged or
    unknown values (for example ADMIN) fall back to STUDENT.
    """
    role = (requested_role or SAFE_DEFAULT_ROLE).strip().upper()
    if role in PUBLIC_REGISTRATION_ROLES:
        return role
    return SAFE_DEFAULT_ROLE


@dataclass(frozen=True)
class JwtSettings:
    secret_key: str
    algorithm: str
    expires_minutes: int


def load_jwt_settings(environment: Optional[str] = None) -> JwtSettings:
    """Load and validate JWT configuration.

    Production (ENVIRONMENT=production) fails fast on a missing, known-default,
    or too-short secret. Development without JWT_SECRET uses an explicit
    development-only default for convenience. Error messages never include the
    configured secret.
    """
    env = (
        environment
        or os.getenv("ENVIRONMENT")
        or os.getenv("APP_ENV")
        or "development"
    ).strip().lower()

    secret = os.getenv("JWT_SECRET")
    if secret is not None:
        secret = secret.strip()

    if not secret:
        if env in PRODUCTION_ENVIRONMENTS:
            raise RuntimeError(
                "JWT_SECRET must be set when ENVIRONMENT=production. "
                "Generate a unique random secret of at least 32 characters."
            )
        secret = DEV_JWT_SECRET

    if env in PRODUCTION_ENVIRONMENTS:
        if secret in KNOWN_INSECURE_SECRETS:
            raise RuntimeError(
                "JWT_SECRET is set to a known insecure default/placeholder. "
                "Generate a unique random secret of at least 32 characters for production."
            )
        if len(secret) < MIN_PRODUCTION_SECRET_LENGTH:
            raise RuntimeError(
                "JWT_SECRET must be at least "
                f"{MIN_PRODUCTION_SECRET_LENGTH} characters in production."
            )

    algorithm = (os.getenv("JWT_ALGORITHM") or "HS256").strip().upper()
    if algorithm not in ALLOWED_ALGORITHMS:
        raise RuntimeError(
            f"Unsupported JWT_ALGORITHM '{algorithm}'. "
            f"Supported algorithms: {', '.join(sorted(ALLOWED_ALGORITHMS))}."
        )

    expires_raw = os.getenv("JWT_EXPIRES_MINUTES", "30").strip()
    try:
        expires_minutes = int(expires_raw)
    except (TypeError, ValueError):
        raise RuntimeError("JWT_EXPIRES_MINUTES must be an integer number of minutes.")

    if not (MIN_TOKEN_MINUTES <= expires_minutes <= MAX_TOKEN_MINUTES):
        raise RuntimeError(
            "JWT_EXPIRES_MINUTES must be between "
            f"{MIN_TOKEN_MINUTES} and {MAX_TOKEN_MINUTES} minutes."
        )

    return JwtSettings(
        secret_key=secret,
        algorithm=algorithm,
        expires_minutes=expires_minutes,
    )


class AuthService:
    def __init__(self, settings: Optional[JwtSettings] = None):
        settings = settings or load_jwt_settings()
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.expires_minutes = settings.expires_minutes

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def create_access_token(self, data: dict) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.expires_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def authenticate(self, email: str, password: str, db: Session) -> Optional[User]:
        """Authenticate a user by email and password."""
        from sqlalchemy.orm import Session as SQLSession
        # Query user by email
        stmt = select(User).where(User.email == email)
        user = db.scalar(stmt)
        
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user

    def get_by_email(self, email: str, db: Session) -> Optional[User]:
        """Return the user with the given email, if one exists."""
        return db.scalar(select(User).where(User.email == email))

    def create(self, user_create: UserCreate, db: Session, role: str = "STUDENT") -> User:
        """Create a user with a server-assigned role.

        The role from public registration input is intentionally ignored; callers
        must pass a role explicitly (only the admin seed does this).
        """
        user = User(
            email=user_create.email,
            password_hash=self.hash_password(user_create.password),
            role=role,
            name=user_create.name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def get_current_user(self, db: Session, token: str) -> User:
        """Get the current user from JWT token."""
        from jwt import PyJWTError
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except PyJWTError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        stmt = select(User).where(User.id == user_id)
        user = db.scalar(stmt)
        
        if user is None:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user

# Create singleton instance
auth_service = AuthService()