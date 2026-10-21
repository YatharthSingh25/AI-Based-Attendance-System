from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Attendance, AttendanceSession, Student
from app.schemas import ConfidenceThreshold


class AttendanceEngine:
    """Dedicated attendance service that handles attendance decision logic.
    
    Decision pipeline:
    Identity valid? → Confidence sufficient? → Liveness valid? → Already marked? → MARK PRESENT
    """
    
    def __init__(self, 
                 confidence_threshold: ConfidenceThreshold = None,
                 liveness_threshold: float = 75.0):
        """Initialize attendance engine.
        
        Args:
            confidence_threshold: Configurable confidence thresholds
            liveness_threshold: Minimum liveness confidence to proceed
        """
        self.confidence_threshold = confidence_threshold or ConfidenceThreshold()
        self.liveness_threshold = liveness_threshold
    
    def decide_attendance(self,
                         student_id: str,
                         session_id: str,
                         recognition_confidence: float,
                         liveness_status: str,
                         db: Session) -> Dict[str, Any]:
        """Make attendance decision based on recognition and liveness.
        
        Decision pipeline:
        1. Identity valid? (student exists in database)
        2. Confidence sufficient? (above review threshold)
        3. Liveness valid? (real face, not spoof)
        4. Already marked? (duplicate check)
        5. MARK PRESENT or return decision reason
        
        Args:
            student_id: Student identifier
            session_id: Attendance session identifier
            recognition_confidence: Recognition confidence percentage (0-100)
            liveness_status: 'real' or 'suspicious'
            db: Database session
            
        Returns:
            Dictionary with attendance decision and details
        """
        # Step 1: Check if student exists
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {
                'decision': 'reject',
                'reason': 'Student not found in database',
                'student_id': student_id,
                'session_id': session_id
            }
        
        # Step 2: Check confidence threshold
        if recognition_confidence >= self.confidence_threshold.high:
            confidence_status = 'high'
        elif recognition_confidence >= self.confidence_threshold.review:
            confidence_status = 'review'
        else:
            confidence_status = 'unknown'
        
        # Step 3: Check liveness
        liveness_valid = liveness_status == 'real'
        if not liveness_valid:
            return {
                'decision': 'reject',
                'reason': 'Liveness check failed - possible spoof detected',
                'student_id': student_id,
                'session_id': session_id,
                'confidence_status': confidence_status,
                'liveness_status': 'suspicious'
            }
        
        # Step 4: Check for duplicate attendance
        existing = db.query(Attendance).filter(
            Attendance.student_id == student_id,
            Attendance.session_id == session_id
        ).first()
        
        if existing:
            return {
                'decision': 'duplicate',
                'reason': 'Student already marked present for this session',
                'student_id': student_id,
                'session_id': session_id,
                'existing_status': existing.status,
                'existing_confidence': existing.confidence
            }
        
        # Step 5: Mark present
        new_attendance = Attendance(
            student_id=student_id,
            session_id=session_id,
            status='present',
            confidence=recognition_confidence,
            method='live' if liveness_valid else 'photo',
            timestamp=datetime.utcnow(),
            verified=True
        )
        
        db.add(new_attendance)
        db.commit()
        db.refresh(new_attendance)
        
        return {
            'decision': 'present',
            'reason': 'Student marked present',
            'student_id': student_id,
            'session_id': session_id,
            'confidence_status': confidence_status,
            'liveness_status': 'real',
            'attendance_id': new_attendance.id
        }
    
    def check_duplicate(self, student_id: str, session_id: str, db: Session) -> bool:
        """Check if a student already has attendance for a session.
        
        Args:
            student_id: Student identifier
            session_id: Attendance session identifier
            db: Database session
            
        Returns:
            True if duplicate exists
        """
        existing = db.query(Attendance).filter(
            Attendance.student_id == student_id,
            Attendance.session_id == session_id
        ).first()
        return existing is not None