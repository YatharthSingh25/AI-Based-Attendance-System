from typing import List, Tuple, Optional, Dict
import numpy as np

# Type aliases
FaceEmbedding = np.ndarray  # Normalized embedding vector
RecognitionResult = Dict  # Contains student info and confidence


class FaceRecognizer:
    """Abstract base class for face recognizers."""
    
    def get_embedding(self, face_image: np.ndarray) -> FaceEmbedding:
        """Generate face embedding from a face image.
        
        Args:
            face_image: Cropped and preprocessed face image (H, W, C)
            
        Returns:
            Normalized face embedding vector
        """
        raise NotImplementedError("Subclasses must implement get_embedding")
    
    def recognize(self, face_embedding: FaceEmbedding) -> List[RecognitionResult]:
        """Recognize a face from its embedding.
        
        Args:
            face_embedding: Normalized face embedding vector
            
        Returns:
            List of recognition results, each containing:
            - 'student_id': Matched student ID
            - 'name': Student name
            - 'confidence': Similarity confidence score (0-100)
            - 'similarity_score': Raw similarity distance/score
        """
        raise NotImplementedError("Subclasses must implement recognize")
    
    def register_embedding(self, student_id: str, embedding: FaceEmbedding) -> bool:
        """Register a new face embedding for a student.
        
        Args:
            student_id: Student identifier
            embedding: Face embedding to register
            
        Returns:
            True if registration successful
        """
        raise NotImplementedError("Subclasses must implement register_embedding")


class MockFaceRecognizer(FaceRecognizer):
    """Mock face recognizer for demonstration purposes.
    
    This simulator generates mock recognition results and is used
    when no real model is available. It can be replaced with
    InsightFace, ArcFace, or deep learning-based recognizers.
    """
    
    def __init__(self, 
                 known_embeddings: Dict[str, FaceEmbedding] = None,
                 threshold: float = 0.6):
        """Initialize mock recognizer.
        
        Args:
            known_embeddings: Dictionary mapping student_id to embedding vectors
            threshold: Similarity threshold for recognition (0-1)
        """
        self.known_embeddings = known_embeddings or {}
        self.threshold = threshold
    
    def get_embedding(self, face_image: np.ndarray) -> FaceEmbedding:
        """Generate mock face embedding from a face image.
        
        In a real implementation, this would use a deep learning model
        (e.g., FaceNet, ArcFace, InsightFace) to generate a 512-dim embedding.
        """
        # Generate a random 512-dimensional embedding normalized to unit length
        embedding = np.random.randn(512)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def recognize(self, face_embedding: FaceEmbedding) -> List[RecognitionResult]:
        """Recognize face from embedding against known students.
        
        Compares the given embedding against all known embeddings
        using cosine similarity and returns matches above threshold.
        
        Args:
            face_embedding: The embedding to recognize
            
        Returns:
            List of recognition results sorted by confidence, each containing:
            - 'student_id': Matched student ID (or 'unknown')
            - 'name': Student name
            - 'confidence': Recognition confidence percentage (0-100)
            - 'similarity_score': Cosine similarity score (0-1)
        """
        results = []
        
        if not self.known_embeddings:
            return [{
                'student_id': 'unknown',
                'name': 'Unknown',
                'confidence': 0.0,
                'similarity_score': 0.0
            }]
        
        # Compute similarity with each known embedding
        for student_id, known_emb in self.known_embeddings.items():
            # Compute cosine similarity
            similarity = np.dot(face_embedding, known_emb)
            similarity = float(np.clip(similarity, -1.0, 1.0))
            
            # Convert to confidence percentage
            # Higher similarity = higher confidence
            confidence = round(float(similarity * 100), 1)
            
            if similarity >= self.threshold:
                results.append({
                    'student_id': student_id,
                    'name': f"Student {student_id}",
                    'confidence': confidence,
                    'similarity_score': similarity
                })
        
        # Sort by confidence (highest first)
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        # If no matches above threshold, return unknown
        if not results:
            return [{
                'student_id': 'unknown',
                'name': 'Unknown',
                'confidence': 0.0,
                'similarity_score': 0.0
            }]
        
        return results
    
    def register_embedding(self, student_id: str, embedding: FaceEmbedding) -> bool:
        """Register a face embedding for a student.
        
        Args:
            student_id: Student identifier
            embedding: Face embedding to store
            
        Returns:
            True if successful
        """
        self.known_embeddings[student_id] = embedding
        return True