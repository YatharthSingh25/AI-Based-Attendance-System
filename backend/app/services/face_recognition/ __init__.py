from services.face_recognition.recognizer import FaceRecognizer
from services.face_recognition.mock import MockFaceRecognizer

# Factory function to get the appropriate recognizer
def get_face_recognizer(model_path: str = None):
    """Get a face recognizer instance.
    
    Args:
        model_path: Path to the face recognition model. 
                    If None, uses MockFaceRecognizer for demo.
    
    Returns:
        FaceRecognizer instance
    """
    if model_path:
        from services.face_recognition.recognizer import ArcFaceRecognizer
        return ArcFaceRecognizer(model_path)
    else:
        from services.face_recognition.mock import MockFaceRecognizer
        return MockFaceRecognizer()