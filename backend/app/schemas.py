from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# Authentication schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: Optional[str] = None
    # Accepted for backward compatibility. Public registration resolves this to
    # STUDENT or FACULTY; privileged/unknown roles become STUDENT. Admins are
    # created only by app.seed_admin.
    role: str = "STUDENT"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    name: Optional[str] = None
    
    class Config:
        from_attributes = True

class StudentCreate(BaseModel):
    student_id: str = Field(min_length=3, max_length=20, pattern="^[A-Z]{3}[0-9]{3}$")
    name: str
    email: EmailStr
    course: str
    branch: str
    section: str
    semester: int

class StudentResponse(BaseModel):
    id: str
    student_id: str
    name: str
    email: str
    course: str
    branch: str
    section: str
    semester: int
    
    class Config:
        from_attributes = True

class AttendanceSessionCreate(BaseModel):
    subject: str
    section: str

class AttendanceSessionResponse(BaseModel):
    id: str
    subject: str
    faculty_id: str
    section: str
    date: datetime
    start_time: datetime
    end_time: datetime
    
    class Config:
        from_attributes = True

class AttendanceCreate(BaseModel):
    student_id: str
    session_id: str
    status: str = "present"
    confidence: Optional[float] = None
    method: str = "live"

class AttendanceResponse(BaseModel):
    id: str
    student_id: str
    session_id: str
    status: str
    confidence: Optional[float] = None
    method: str
    timestamp: datetime
    verified: bool
    
    class Config:
        from_attributes = True

class ConfidenceThreshold(BaseModel):
    """Configurable confidence thresholds."""
    high: float = 90.0  # >= 90% → High confidence
    review: float = 75.0  # 75-89% → Review
    unknown: float = 75.0  # < 75% → Unknown

class AuditLogCreate(BaseModel):
    attendance_id: str
    action: str
    performed_by: str
    details: Optional[str] = None

class MLTrainRequest(BaseModel):
    model_type: str = "logistic_regression"

class MLTrainResponse(BaseModel):
    message: str
    accuracy: float
    model_type: str

class MLPredictionResponse(BaseModel):
    student_id: str
    name: str
    overall_percentage: float
    risk_level: str  # LOW, MEDIUM, HIGH

class ErrorResponse(BaseModel):
    detail: str
    code: str