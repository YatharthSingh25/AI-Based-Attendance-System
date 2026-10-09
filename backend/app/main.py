from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import bcrypt

from database import get_db
from models import User, Student, AttendanceSession, Attendance, FaceEmbedding
from schemas import UserCreate, UserLogin, StudentCreate, AttendanceCreate
from services import auth_service

app = FastAPI(
    title="AI Attendance System API",
    version="1.0.0",
    description="Intelligent Classroom Attendance System"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
    user = auth_service.create(user_create, db)
    return {
        "message": "User registered successfully",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.name
        }
    }

@app.get("/api/students", response_model=List[dict])
async def get_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
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
    current_user: User = Depends(auth_service.get_current_user)
):
    """Create a new student."""
    # Check if student_id already exists
    existing = db.query(Student).filter(Student.student_id == student.student_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID already exists"
        )
    from models import UserRole
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
    current_user: User = Depends(auth_service.get_current_user)
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
    current_user: User = Depends(auth_service.get_current_user)
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
    current_user: User = Depends(auth_service.get_current_user)
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
    current_user: User = Depends(auth_service.get_current_user)
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
    from models import FaceEmbedding
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
    subject: str,
    section: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """Create a new attendance session."""
    from models import AttendanceSession
    # Generate session ID
    session_id = f"session_{datetime.utcnow().timestamp()}"
    new_session = AttendanceSession(
        session_id=session_id,
        subject=subject,
        faculty_id=current_user.id,
        section=section,
        date=datetime.utcnow().date(),
        start_time=datetime.utcnow().time(),
        end_time=(datetime.utcnow() + timedelta(hours=2)).time()
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
    current_user: User = Depends(auth_service.get_current_user)
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
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get attendance records for a specific session."""
    from models import Attendance
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
    session_id: str,
    image_data: bytes,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """Process classroom photo for attendance."""
    # TODO: Integrate with face detection/recognition service
    # For now, return placeholder
    return {
        "message": "Photo attendance processing - AI service integration pending",
        "session_id": session_id
    }

@app.post("/api/attendance/live/frame", response_model=dict)
async def live_frame(
    session_id: str,
    frame_data: bytes,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """Process a single frame from live camera for attendance."""
    # TODO: Integrate with face detection/recognition service
    return {
        "message": "Live frame processing - AI service integration pending",
        "session_id": session_id
    }

@app.post("/api/attendance/{attendance_id}/review", response_model=dict)
async def review_attendance(
    attendance_id: str,
    action: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """Teacher review of attendance - confirm, change, or reject."""
    from models import Attendance
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Record in audit log
    from models import AuditLog
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
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get analytics overview."""
    from sqlalchemy import func
    from models import Attendance, AttendanceSession
    
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
    percentage = Math.round((present_count / total_attendance) * 100) if total_attendance > 0 else 0
    
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
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get analytics for a specific student."""
    from models import Attendance, AttendanceSession
    
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
    percentage = Math.round((attended / total) * 100)
    
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
    current_user: User = Depends(auth_service.get_current_user)
):
    """Train ML model for attendance risk prediction."""
    from models import Attendance, AttendanceSession
    from services import ml_service
    
    # Get historical attendance data
    records = db.query(Attendance, AttendanceSession).join(
        AttendanceSession, Attendance.session_id == AttendanceSession.session_id
    ).all()
    
    if len(records) < 10:
        return {
            "message": "Insufficient historical data for reliable ML prediction.",
            "accuracy": 0
        }
    
    # Train model
    result = ml_service.train(records)
    
    return {
        "message": "ML model trained successfully",
        "accuracy": result.get("accuracy", 0),
        "model_type": result.get("model_type", "logistic_regression")
    }

@app.get("/api/ml/predictions", response_model=List[dict])
async def ml_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get attendance risk predictions."""
    from models import Student, Attendance
    
    students = db.query(Student).all()
    predictions = []
    
    for student in students:
        records = db.query(Attendance).filter(Attendance.student_id == student.student_id).all()
        if len(records) == 0:
            continue
        
        attended = sum(1 for r in records if r.status == 'present')
        total = len(records)
        percentage = Math.round((attended / total) * 100) if total > 0 else 0
        
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