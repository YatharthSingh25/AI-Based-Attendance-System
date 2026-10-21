from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_db, create_db_and_tables
from app.models import User, Student, AttendanceSession, Attendance, FaceEmbedding
from app.schemas import (
    UserCreate,
    UserLogin,
    StudentCreate,
    AttendanceSessionCreate,
    MLPredictionResponse,
)
from app.core.auth import auth_service, resolve_public_registration_role

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure required tables exist before serving requests."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="AI Attendance System API",
    version="1.0.0",
    description="Intelligent Classroom Attendance System",
    lifespan=lifespan,
)

# CORS configuration
# In production, set CORS_ORIGINS environment variable as comma-separated list
# e.g., "http://localhost:3000,http://my-app.vercel.app"
import os

def get_cors_origins():
    """Parse CORS origins from environment variable."""
    origins_str = os.getenv("CORS_ORIGINS", "")
    if origins_str:
        return [o.strip() for o in origins_str.split(",") if o.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

origins = get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    return auth_service.get_current_user(db, token)


def require_roles(*allowed_roles: str):
    """Build a dependency that allows only the listed roles.

    Authentication runs first via ``get_current_user`` (401 when no valid
    token is present). Authenticated users without an allowed role receive 403.
    """
    allowed = frozenset(role.strip().upper() for role in allowed_roles)
    if not allowed:
        raise ValueError("require_roles requires at least one role")

    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        role = (current_user.role or "").strip().upper()
        if role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_dependency


@app.get("/health", include_in_schema=False)
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Attendance System API",
        "version": "1.0.0"
    }

@app.post("/api/auth/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint - authenticates user and returns JWT token."""
    user = auth_service.authenticate(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id)}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.name
        }
    }

@app.post("/api/auth/register", response_model=dict)
async def register(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    existing_user = auth_service.get_by_email(user_create.email, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    # Public registration may create STUDENT or FACULTY accounts only.
    # Privileged/unknown roles (including ADMIN) fall back to STUDENT; ADMIN
    # accounts are provisioned only through the environment-based seed process.
    public_role = resolve_public_registration_role(user_create.role)
    user = auth_service.create(user_create, db, role=public_role)
    return {
        "message": "User registered successfully",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.name
        }
    }

@app.get("/api/students", response_model=None)
async def get_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Get all students."""
    students = db.query(Student).all()
    return [
        {
            "id": str(s.id),
            "student_id": s.student_id,
            "name": s.name,
            "email": s.email,
            "course": s.course,
            "branch": s.branch,
            "section": s.section,
            "semester": s.semester
        }
        for s in students
    ]

@app.post("/api/students", response_model=dict)
async def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Create a new student."""
    # Check if student_id already exists
    existing = db.query(Student).filter(Student.student_id == student.student_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID already exists"
        )
    new_student = Student(
        student_id=student.student_id,
        name=student.name,
        email=student.email,
        course=student.course,
        branch=student.branch,
        section=student.section,
        semester=student.semester
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {
        "message": "Student created successfully",
        "student": {
            "id": str(new_student.id),
            "student_id": new_student.student_id,
            "name": new_student.name,
            "email": new_student.email,
            "course": new_student.course,
            "branch": new_student.branch,
            "section": new_student.section,
            "semester": new_student.semester
        }
    }

@app.get("/api/students/{student_id}", response_model=dict)
async def get_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Get a specific student by ID."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return {
        "id": str(student.id),
        "student_id": student.student_id,
        "name": student.name,
        "email": student.email,
        "course": student.course,
        "branch": student.branch,
        "section": student.section,
        "semester": student.semester
    }

@app.put("/api/students/{student_id}", response_model=dict)
async def update_student(
    student_id: str,
    student_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Update student information."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    for key, value in student_update.items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return {
        "message": "Student updated successfully",
        "student": {
            "id": str(student.id),
            "student_id": student.student_id,
            "name": student.name,
            "email": student.email,
            "course": student.course,
            "branch": student.branch,
            "section": student.section,
            "semester": student.semester
        }
    }

@app.delete("/api/students/{student_id}")
async def delete_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Delete a student."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}

@app.post("/api/students/{student_id}/enroll-face")
async def enroll_face(
    student_id: str,
    images: list,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Enroll face images for a student."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    # TODO: Process images and generate face embeddings
    # For now, store placeholder
    from app.models import FaceEmbedding
    embedding = FaceEmbedding(
        student_id=student.id,
        embedding_vector=[],  # Will be populated by AI service
        image_paths=[],  # Will store paths to enrolled images
        created_at=datetime.utcnow()
    )
    db.add(embedding)
    db.commit()
    return {
        "message": "Face enrollment placeholder - embeddings to be generated by AI service",
        "student_id": student_id
    }

@app.post("/api/attendance/sessions", response_model=dict)
async def create_attendance_session(
    session_data: AttendanceSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Create a new attendance session."""
    from app.models import AttendanceSession
    # Generate session ID
    session_id = f"session_{datetime.utcnow().timestamp()}"
    new_session = AttendanceSession(
        session_id=session_id,
        subject=session_data.subject,
        faculty_id=current_user.id,
        section=session_data.section,
        date=datetime.utcnow().date(),
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2)
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {
        "message": "Attendance session created successfully",
        "session": {
            "id": new_session.session_id,
            "subject": new_session.subject,
            "section": new_session.section,
            "date": new_session.date,
            "start_time": new_session.start_time,
            "end_time": new_session.end_time
        }
    }

@app.get("/api/attendance/sessions", response_model=List[dict])
async def get_attendance_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Get all attendance sessions."""
    sessions = db.query(AttendanceSession).all()
    return [
        {
            "id": s.session_id,
            "subject": s.subject,
            "faculty": s.faculty_id,
            "section": s.section,
            "date": s.date,
            "start_time": s.start_time,
            "end_time": s.end_time
        }
        for s in sessions
    ]

@app.get("/api/attendance/{session_id}", response_model=List[dict])
async def get_attendance_by_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Get attendance records for a specific session."""
    from app.models import Attendance
    attendance = db.query(Attendance).filter(Attendance.session_id == session_id).all()
    return [
        {
            "id": a.id,
            "student_id": a.student_id,
            "status": a.status,
            "confidence": a.confidence,
            "method": a.method,
            "timestamp": a.timestamp,
            "verified": a.verified
        }
        for a in attendance
    ]

@app.post("/api/attendance/photo", response_model=dict)
async def attendance_photo(
    session_id: str = Form(...),
    image_data: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Process classroom photo for attendance."""
    # TODO: Integrate with face detection/recognition service
    # For now, accept the upload and return a placeholder.
    contents = await image_data.read()
    return {
        "message": "Photo attendance processing - AI service integration pending",
        "session_id": session_id,
        "filename": image_data.filename,
        "size_bytes": len(contents)
    }

@app.post("/api/attendance/live/frame", response_model=dict)
async def live_frame(
    session_id: str = Form(...),
    frame_data: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Process a single frame from live camera for attendance."""
    # TODO: Integrate with face detection/recognition service
    contents = await frame_data.read()
    return {
        "message": "Live frame processing - AI service integration pending",
        "session_id": session_id,
        "filename": frame_data.filename,
        "size_bytes": len(contents)
    }

@app.post("/api/attendance/{attendance_id}/review", response_model=dict)
async def review_attendance(
    attendance_id: str,
    action: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Teacher review of attendance - confirm, change, or reject."""
    from app.models import Attendance
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Record in audit log
    from app.models import AuditLog
    audit = AuditLog(
        attendance_id=attendance.id,
        action=action,
        performed_by=current_user.id,
        timestamp=datetime.utcnow(),
        details=f"Attendance review: {action}"
    )
    db.add(audit)
    
    if action == "confirm":
        attendance.status = "present"
        attendance.verified = True
    elif action == "reject":
        attendance.status = "absent"
        attendance.verified = False
    elif action == "change":
        # Would need new student assignment
        attendance.status = "review"
    
    db.commit()
    db.refresh(attendance)
    
    return {
        "message": f"Attendance {action} successfully",
        "attendance": {
            "id": attendance.id,
            "student_id": attendance.student_id,
            "status": attendance.status,
            "confidence": attendance.confidence,
            "verified": attendance.verified
        }
    }

@app.get("/api/analytics/overview", response_model=dict)
async def analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Get analytics overview."""
    from sqlalchemy import func
    from app.models import Attendance, AttendanceSession
    
    # Total sessions
    total_sessions = db.query(AttendanceSession).count()
    
    # Overall attendance
    result = db.query(
        func.count(Attendance.student_id).filter(Attendance.status == 'present').label('present'),
        func.count(Attendance.student_id).filter(Attendance.status == 'absent').label('absent'),
        func.count(Attendance.student_id).filter(Attendance.status == 'unknown').label('unknown')
    ).first()
    
    total_attendance = result.present + result.absent + result.unknown
    present_count = result.present or 0
    absent_count = result.absent or 0
    unknown_count = result.unknown or 0
    percentage = round((present_count / total_attendance) * 100) if total_attendance > 0 else 0
    
    return {
        "total_sessions": total_sessions,
        "present": present_count,
        "absent": absent_count,
        "unknown": unknown_count,
        "overall_percentage": percentage
    }

@app.get("/api/analytics/student/{student_id}", response_model=dict)
async def analytics_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Get analytics for a specific student."""
    from app.models import Attendance, AttendanceSession
    
    # Get all attendance records for this student
    records = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    
    total = len(records)
    if total == 0:
        return {
            "student_id": student_id,
            "overall_percentage": 0,
            "subjects": [],
            "classes_attended": 0,
            "classes_missed": 0,
            "risk_level": "LOW"
        }
    
    attended = sum(1 for r in records if r.status == 'present')
    missed = sum(1 for r in records if r.status == 'absent')
    percentage = round((attended / total) * 100)
    
    # Get subjects
    subjects = list(set(r.session.subject for r in records if r.session))
    
    # Determine risk level
    if percentage >= 80:
        risk_level = "LOW"
    elif percentage >= 60:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
    
    return {
        "student_id": student_id,
        "overall_percentage": percentage,
        "subjects": subjects,
        "classes_attended": attended,
        "classes_missed": missed,
        "risk_level": risk_level
    }

@app.post("/api/ml/train", response_model=dict)
async def ml_train(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    """Report that ML training is unavailable; no model is trained."""
    from app.models import Attendance, AttendanceSession
    from app.services.ml.service import MLServices

    # Count historical data so the response can report it truthfully. The
    # bundled service is not a validated training pipeline (its target labels do
    # not match attendance statuses), so do not call train() or claim success.
    records = db.query(Attendance, AttendanceSession).join(
        AttendanceSession, Attendance.session_id == AttendanceSession.session_id
    ).all()

    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "message": (
                "ML training is not implemented in this build. "
                "No model was trained and no predictions were generated."
            ),
            "training_performed": False,
            "accuracy": 0,
            "model_type": None,
            "data_points": len(records),
            "service_available": MLServices.training_available(),
        },
    )

@app.get("/api/ml/predictions", response_model=List[MLPredictionResponse])
async def ml_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Get attendance risk predictions."""
    from app.models import Student, Attendance
    
    students = db.query(Student).all()
    predictions = []
    
    for student in students:
        records = db.query(Attendance).filter(Attendance.student_id == student.student_id).all()
        if len(records) == 0:
            continue
        
        attended = sum(1 for r in records if r.status == 'present')
        total = len(records)
        percentage = round((attended / total) * 100) if total > 0 else 0
        
        if percentage >= 80:
            risk_level = "LOW"
        elif percentage >= 60:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        predictions.append({
            "student_id": student.student_id,
            "name": student.name,
            "overall_percentage": percentage,
            "risk_level": risk_level
        })
    
    return predictions


# === Settings Endpoints ===

@app.get("/api/settings/thresholds", response_model=dict)
async def get_thresholds(
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Get current recognition confidence thresholds."""
    return {
        "highConfidence": 90,
        "reviewThreshold": 75,
        "unknownThreshold": 75,
        "description": ">= 90% → High confidence, 75-89% → Review, < 75% → Unknown"
    }

@app.post("/api/settings/thresholds", response_model=dict)
async def update_thresholds(
    thresholds: dict,
    current_user: User = Depends(require_roles("ADMIN"))
):
    """Update recognition confidence thresholds.

    In production, this would save to database/config.
    Currently accepts and acknowledges the update.
    """
    high = thresholds.get("highConfidence", 90)
    review = thresholds.get("reviewThreshold", 75)
    unknown = thresholds.get("unknownThreshold", 75)
    # Validate ranges
    if not (90 <= high <= 100):
        raise HTTPException(status_code=400, detail="highConfidence must be between 90 and 100")
    if not (75 <= review <= 99):
        raise HTTPException(status_code=400, detail="reviewThreshold must be between 75 and 99")
    if not (0 <= unknown <= 74):
        raise HTTPException(status_code=400, detail="unknownThreshold must be between 0 and 74")
    return {
        "message": "Confidence thresholds updated (demo mode - saved to session)",
        "highConfidence": high,
        "reviewThreshold": review,
        "unknownThreshold": unknown
    }

@app.get("/api/settings/liveness", response_model=dict)
async def get_liveness_settings(
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Get liveness/anti-spoofing configuration."""
    return {
        "enabled": True,
        "spoofThreshold": 0.5,
        "description": "Liveness is an additional verification layer and is not guaranteed to stop every attack"
    }

@app.post("/api/settings/liveness", response_model=dict)
async def update_liveness_settings(
    settings: dict,
    current_user: User = Depends(require_roles("ADMIN"))
):
    """Update liveness/anti-spoofing configuration.

    In production, this would save to database/config.
    Currently acknowledges the update with disclaimer.
    """
    enabled = settings.get("enabled", True)
    spoof_threshold = settings.get("spoofThreshold", 0.5)
    return {
        "message": "Liveness settings updated (demo mode - saved to session)",
        "enabled": enabled,
        "spoofThreshold": spoof_threshold,
        "disclaimer": "Liveness is an additional verification layer and is not guaranteed to stop every attack"
    }

@app.get("/api/settings/ml", response_model=dict)
async def get_ml_settings(
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Get machine learning attendance risk prediction configuration."""
    return {
        "model": "logistic_regression",
        "autoTrain": False,
        "description": "Models: Logistic Regression, Random Forest, XGBoost. Features: current_attendance, classes_attended, classes_missed, recent_attendance, consecutive_absences, subject_attendance, attendance_trend. Output: LOW RISK, MEDIUM RISK, HIGH RISK (attendance shortage only)"
    }

@app.post("/api/settings/ml", response_model=dict)
async def update_ml_settings(
    settings: dict,
    current_user: User = Depends(require_roles("ADMIN"))
):
    """Update machine learning attendance risk prediction configuration.

    In production, this would train and save the model.
    Currently acknowledges the update with explanation of limitations.
    """
    model = settings.get("model", "logistic_regression")
    auto_train = settings.get("autoTrain", False)
    return {
        "message": "ML settings updated (demo mode - no model trained without model files)",
        "model": model,
        "autoTrain": auto_train,
        "note": "Model files not present in repository. Real ML prediction requires trained model weights.",
        "warning": "Insufficient historical data for reliable ML prediction if no model trained"
    }

@app.post("/api/reports/export", response_model=dict)
async def export_report(
    request: dict,
    current_user: User = Depends(require_roles("FACULTY", "ADMIN"))
):
    """Export attendance report in specified format.

    Formats: PDF, CSV, Excel

    In production, this would generate and download a file.
    Currently returns a description and acknowledges the request.
    """
    format_type = request.get("format", "PDF")
    valid_formats = ["PDF", "CSV", "Excel"]
    if format_type not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
        )
    return {
        "message": f"Report export requested as {format_type} (demo mode - file generation pending)",
        "format": format_type,
        "note": "Report generation requires actual attendance data and file formatting logic.",
        "disclaimer": "No files are generated in demo mode. Real report export requires backend implementation."
    }