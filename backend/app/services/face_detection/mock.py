from typing import List, Tuple, Optional
import numpy as np

# Type aliases for face detection results
FaceBox = Tuple[int, int, int, int]  # (x, y, width, height)
FaceDetection = dict  # Contains bounding box and confidence


class FaceDetector:
    """Abstract base class for face detectors."""
    
    def detect_faces(self, image: np.ndarray) -> List[FaceDetection]:
        """Detect faces in an image.
        
        Args:
            image: Input image as numpy array (H, W, C)
            
        Returns:
            List of face detections, each containing:
            - 'box': (x, y, w, h) bounding box coordinates
            - 'confidence': Detection confidence score
        """
        raise NotImplementedError("Subclasses must implement detect_faces")
    
    def detect_faces_from_bytes(self, image_bytes: bytes) -> List[FaceDetection]:
        """Detect faces from image bytes.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            List of face detections
        """
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return self.detect_faces(image)


class MockFaceDetector(FaceDetector):
    """Mock face detector for demonstration purposes.
    
    This simulator detects a configurable number of faces and is used
    when no real model is available. It can be replaced with OpenCV,
    InsightFace, or YOLO-based detectors without changing the API.
    """
    
    def __init__(self, num_faces: int = 3):
        self.num_faces = num_faces
    
    def detect_faces(self, image: np.ndarray) -> List[FaceDetection]:
        """Detect mock faces in an image.
        
        Generates synthetic face detections for demonstration.
        In production, this would use a real face detection model.
        """
        h, w = image.shape[:2]
        detections = []
        
        for i in range(self.num_faces):
            # Generate random bounding box within image bounds
            x = np.random.randint(0, w // 4)
            y = np.random.randint(0, h // 4)
            width = np.random.randint(w // 6, w // 3)
            height = np.random.randint(h // 6, h // 3)
            
            # Ensure box stays within image boundaries
            x = min(x, w - width - 10)
            y = min(y, h - height - 10)
            
            confidence = round(float(np.random.uniform(70, 100)), 1)
            
            detections.append({
                'box': (x, y, width, height),
                'confidence': confidence
            })
        
        return detections


class OpenCVFaceDetector(FaceDetector):
    """OpenCV-based face detector using Haar Cascades or DNN."""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        # Would initialize cv2.CascadeClassifier or cv2.dnn here
        # self.face_cascade = cv2.CascadeClassifier(model_path)
    
    def detect_faces(self, image: np.ndarray) -> List[FaceDetection]:
        """Detect faces using OpenCV."""
        # Placeholder - would use actual OpenCV face detection
        # faces = self.face_cascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5)
        # return [{'box': (x, y, w, h), 'confidence': float(conf)} for (x, y, w, h) in faces]
        raise NotImplementedError("OpenCV face detector - implement model loading")


class InsightFaceDetector(FaceDetector):
    """InsightFace-based face detector."""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        # Would initialize InsightFace model here
    
    def detect_faces(self, image: np.ndarray) -> List[FaceDetection]:
        """Detect faces using InsightFace."""
        # Placeholder - would use actual InsightFace detection
        raise NotImplementedError("InsightFace detector - implement model loading")