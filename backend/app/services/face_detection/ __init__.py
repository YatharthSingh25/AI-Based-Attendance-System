from services.face_detection.detector import FaceDetector
from services.face_detection.mock import MockFaceDetector

# Factory function to get the appropriate detector
def get_face_detector(model_path: str = None):
    """Get a face detector instance.
    
    Args:
        model_path: Path to the face detection model. 
                    If None, uses MockFaceDetector for demo.
    
    Returns:
        FaceDetector instance
    """
    if model_path and model_path.endswith(('.pb', '.tflite', '.onnx')):
        from services.face_detection.detector import OpenCVFaceDetector
        return OpenCVFaceDetector(model_path)
    elif model_path:
        from services.face_detection.detector import InsightFaceDetector
        return InsightFaceDetector(model_path)
    else:
        from services.face_detection.mock import MockFaceDetector
        return MockFaceDetector()