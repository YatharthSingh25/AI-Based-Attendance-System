import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from models import User
from schemas import UserCreate, UserLogin

class AuthService:
    def __init__(self, secret_key: str = "attendance-ai-secret-key-2026", 
                 algorithm: str = "HS256", 
                 expires_minutes: int = 30):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expires_minutes = expires_minutes
    
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
        
        stmt = select(User).where(User.id == int(user_id))
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