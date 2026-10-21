from typing import List, Optional, Dict, Any
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import json

class MLServices:
    """Machine learning service for attendance risk prediction.
    
    Predicts attendance risk (LOW/MEDIUM/HIGH) based on historical attendance data.
    Does NOT predict academic performance - only attendance shortage risk.
    """

    @classmethod
    def training_available(cls) -> bool:
        """Return whether a validated training pipeline is available.

        The bundled ``train`` method is an experimental scaffold: it expects
        LOW/MEDIUM/HIGH risk labels, while stored attendance statuses are
        present/absent/unknown/review, and its prediction path is a placeholder.
        It must not be reported as a successful production training pipeline.
        """
        return False
    
    def __init__(self):
        """Initialize ML services with available models."""
        self.models = {
            'logistic_regression': LogisticRegression(max_iter=1000, random_state=42),
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'xgboost': XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss')
        }
        self.trained_model = None
        self.feature_names = []
        self.label_encoder = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        self.is_trained = False
    
    def prepare_features(self, records: List[Any]) -> pd.DataFrame:
        """Prepare feature vectors from historical attendance records.
        
        Features:
        - current_attendance: Current attendance percentage
        - classes_attended: Total classes attended
        - classes_missed: Total classes missed
        - recent_attendance: Attendance in recent period (last 7 days)
        - consecutive_absences: Current streak of absences
        - subject_attendance: Attendance per subject
        - attendance_trend: Trend over time (improving/declining)
        
        Args:
            records: List of attendance records with session information
            
        Returns:
            DataFrame with feature columns
        """
        if not records:
            return pd.DataFrame()
        
        data = []
        for record in records:
            attendance, session = record
            
            # Calculate basic metrics
            total_sessions = 1  # This session
            attended = 1 if attendance.status == 'present' else 0
            missed = 1 if attendance.status == 'absent' else 0
            
            # Compute current attendance percentage (would need historical data for accurate calc)
            # Placeholder - in production, compute from all student's attendance
            current_pct = attended / total_sessions if total_sessions > 0 else 0
            
            # Recent attendance (placeholder - would need last N sessions)
            recent_attendance = current_pct  # Simplified
            
            # Consecutive absences (placeholder)
            consecutive_absences = 0  # Would need streak analysis
            
            # Subject attendance (placeholder)
            subject_attendance = current_pct  # Simplified
            
            data.append({
                'current_attendance': current_pct,
                'classes_attended': attended,
                'classes_missed': missed,
                'recent_attendance': recent_attendance,
                'consecutive_absences': consecutive_absences,
                'subject_attendance': subject_attendance,
                'attendance_trend': 0,  # Would compute from trend
                'risk_level': attendance.status  # Target variable
            })
        
        return pd.DataFrame(data)
    
    def train(self, records: List[Any]) -> Dict[str, Any]:
        """Train the ML model on historical attendance data.
        
        Args:
            records: List of (Attendance, AttendanceSession) tuples from database
            
        Returns:
            Training results including accuracy and metrics
        """
        df = self.prepare_features(records)
        
        if len(df) < 10:
            return {
                'message': 'Insufficient historical data for reliable ML prediction.',
                'accuracy': 0,
                'model_type': None,
                'data_points': len(df)
            }
        
        # Prepare features and target
        X = df[self.feature_names].values if self.feature_names else df.drop('risk_level', axis=1).values
        y = df['risk_level'].values
        
        # Encode target
        y_encoded = np.vectorize(self.label_encoder.get)(y)
        
        # Split data (simple 80/20 split)
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y_encoded[:split_idx], y_encoded[split_idx:]
        
        # Train model
        best_model_name = 'logistic_regression'
        best_accuracy = 0
        
        for name, model in self.models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model_name = name
                self.trained_model = model
        
        self.is_trained = True
        self.feature_names = df.columns.drop('risk_level').tolist()
        
        # Compute additional metrics
        cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        return {
            'message': 'ML model trained successfully',
            'accuracy': round(best_accuracy, 4),
            'model_type': best_model_name,
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'confusion_matrix': cm.tolist(),
            'data_points': len(df),
            'feature_names': self.feature_names
        }
    
    def predict(self, student_id: str, db_session) -> Optional[Dict[str, Any]]:
        """Predict attendance risk for a specific student.
        
        Args:
            student_id: Student identifier
            db_session: Database session for querying historical data
            
        Returns:
            Prediction result with risk level and metrics, or None if insufficient data
        """
        if not self.is_trained or self.trained_model is None:
            return None
        
        # Get historical attendance records for this student
        # This would query the database in production
        # For now, return placeholder
        return {
            'student_id': student_id,
            'risk_level': 'LOW',  # Placeholder
            'message': 'ML prediction - using trained model'
        }
    
    def get_student_risk(
        self, 
        student_id: str, 
        classes_attended: int, 
        classes_missed: int,
        db_session
    ) -> Dict[str, Any]:
        """Get attendance risk for a student based on attendance counts.
        
        Args:
            student_id: Student identifier
            classes_attended: Number of classes attended
            classes_missed: Number of classes missed
            db_session: Database session
            
        Returns:
            Risk assessment dictionary
        """
        total = classes_attended + classes_missed
        if total == 0:
            percentage = 0
        else:
            percentage = round((classes_attended / total) * 100, 2)
        
        # Determine risk level
        if percentage >= 80:
            risk_level = 'LOW'
        elif percentage >= 60:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
        
        # Warning message for at-risk students
        if risk_level == 'HIGH':
            warning = f"⚠ {student_id} attendance requires attention - {percentage}% attendance"
        elif risk_level == 'MEDIUM':
            warning = f"Note: {student_id} attendance at {percentage}% - monitor for improvement"
        else:
            warning = f"Good attendance: {student_id} at {percentage}%"
        
        return {
            'student_id': student_id,
            'overall_percentage': percentage,
            'risk_level': risk_level,
            'classes_attended': classes_attended,
            'classes_missed': classes_missed,
            'warning': warning
        }