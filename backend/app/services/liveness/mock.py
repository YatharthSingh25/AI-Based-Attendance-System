from typing import Optional, Dict
import numpy as np

LivenessResult = Dict[str, str]  # {'status': 'real' | 'suspicious', 'confidence': float}


class LivenessDetector:
    """Abstract base class for liveness detectors."""
    
    def check_liveness(self, face_image: np.ndarray) -> LivenessResult:
        """Check if a face is live (real) or spoofed.
        
        Args:
            face_image: Cropped face image array
            
        Returns:
            Liveness result containing:
            - 'status': 'real' or 'suspicious'
            - 'confidence': Confidence score (0-100)
        """
        raise NotImplementedError("Subclasses must implement check_liveness")
    
    def check_liveness_from_bytes(self, image_bytes: bytes) -> LivenessResult:
        """Check liveness from image bytes.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Liveness result
        """
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return self.check_liveness(image)


class MockLivenessDetector(LivenessDetector):
    """Mock liveness detector for demonstration.
    
    This simulator provides mock liveness checks and can be replaced
    with a real liveness/anti-spoofing model.
    """
    
    def __init__(self, spoof_threshold: float = 0.5):
        """Initialize mock liveness detector.
        
        Args:
            spoof_threshold: Threshold for determining spoofing (0-1)
        """
        self.spoof_threshold = spoof_threshold
    
    def check_liveness(self, face_image: np.ndarray) -> LivenessResult:
        """Check liveness of a face.
        
        In a real implementation, this would use a trained anti-spoofing model
        that analyzes texture, depth, reflections, and other realness cues.
        
        For demo purposes, randomly determines real/spoof status.
        """
        # Mock: 95% of the time it's real, 5% suspicious
        import random
        is_real = random.random() > 0.05
        
        if is_real:
            confidence = round(random.uniform(85, 100), 1)
            return {
                'status': 'real',
                'confidence': confidence
            }
        else:
            confidence = round(random.uniform(50, 80), 1)
            return {
                'status': 'suspicious',
                'confidence': confidence
            }