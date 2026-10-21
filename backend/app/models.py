from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="STUDENT")  # ADMIN, FACULTY, STUDENT
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    students = relationship("Student", foreign_keys="Student.faculty_id", back_populates="faculty")
    taught_sessions = relationship("AttendanceSession", foreign_keys="AttendanceSession.faculty_id", back_populates="faculty")

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)  # e.g., CSE001
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    course = Column(String, nullable=False)
    branch = Column(String, nullable=False)  # e.g., CSE, ECE, etc.
    section = Column(String, nullable=False)  # e.g., A, B, C
    semester = Column(Integer, nullable=False)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    faculty = relationship("User", foreign_keys=[faculty_id], back_populates="students")
    embeddings = relationship("FaceEmbedding", back_populates="student")
    attendance_records = relationship("Attendance", back_populates="student")

class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    embedding_vector = Column(String, nullable=False)  # JSON string of numpy array
    image_paths = Column(Text, nullable=True)  # Comma-separated paths
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="embeddings")

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)  # e.g., session_12345
    subject = Column(String, nullable=False)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    section = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Relationships
    faculty = relationship("User", foreign_keys=[faculty_id], back_populates="taught_sessions")
    attendance = relationship("Attendance", back_populates="session")

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_id = Column(String, ForeignKey("attendance_sessions.session_id"), nullable=False)
    status = Column(String, nullable=False)  # present, absent, unknown, review
    confidence = Column(Float, nullable=True)  # Recognition confidence percentage
    method = Column(String, nullable=False)  # photo, live
    timestamp = Column(DateTime, default=func.now())
    verified = Column(Boolean, default=False)
    
    # Constraints and Relationships
    __table_args__ = (
        UniqueConstraint('student_id', 'session_id', name='_student_session_uc'),
    )
    
    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    session = relationship("AttendanceSession", back_populates="attendance")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    attendance_id = Column(Integer, ForeignKey("attendance.id"), nullable=True)
    action = Column(String, nullable=False)  # confirm, reject, change, etc.
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    details = Column(Text, nullable=True)

class Timetable(Base):
    __tablename__ = "timetable"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("attendance_sessions.session_id"), nullable=False)
    day_of_week = Column(String, nullable=False)
    period = Column(Integer, nullable=False)
    classroom = Column(String, nullable=True)

class MLPrediction(Base):
    __tablename__ = "ml_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    risk_level = Column(String, nullable=False)  # LOW, MEDIUM, HIGH
    predicted_at = Column(DateTime, default=func.now())
    accuracy = Column(Float, nullable=True)