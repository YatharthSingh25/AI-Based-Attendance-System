from typing import Dict, Optional, Tuple
import numpy as np

# Types for tracking
TrackID = str
StudentID = str
FrameData = Dict

class FaceTracker:
    """Abstract base class for face trackers."""
    
    def update(self, detections: List[dict], frame_number: int) -> List[dict]:
        """Update tracking with new detections.
        
        Args:
            detections: List of face detection results from current frame
            frame_number: Current frame number
            
        Returns:
            List of tracked faces with track_id added
        """
        raise NotImplementedError("Subclasses must implement update")
    
    def get_tracked_face(self, track_id: TrackID) -> Optional[dict]:
        """Get tracked face information by track ID.
        
        Args:
            track_id: The tracking ID
            
        Returns:
            Tracked face data or None
        """
        raise NotImplementedError("Subclasses must implement get_tracked_face")


class SimpleFaceTracker(FaceTracker):
    """Simple face tracker that assigns stable track IDs to detected faces.
    
    Uses a simple matching algorithm based on IoU (Intersection over Union)
    between detected faces across frames. In production, this would be replaced
    with DeepSORT or similar tracking algorithms.
    """
    
    def __init__(self, max_disappeared: int = 10, max_distance: float = 0.6):
        """Initialize the face tracker.
        
        Args:
            max_disappeared: Maximum number of frames a face can disappear before removal
            max_distance: Maximum distance threshold for matching faces
        """
        self.next_track_id = 1
        self.tracks: Dict[TrackID, dict] = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self.frame_count = 0
    
    def _compute_iou(self, box1: Tuple[int, int, int, int], 
                     box2: Tuple[int, int, int, float]) -> float:
        """Compute Intersection over Union between two bounding boxes.
        
        Args:
            box1: (x, y, w, h) first box
            box2: (x, y, w, h) second box
            
        Returns:
            IoU value between 0 and 1
        """
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - intersection_area
        
        if union_area == 0:
            return 0.0
        
        return intersection_area / union_area
    
    def update(self, detections: List[dict], frame_number: int) -> List[dict]:
        """Update tracking with new detections.
        
        Args:
            detections: List of face detection results from current frame
            frame_number: Current frame number
            
        Returns:
            List of tracked faces with track_id and student_id added
        """
        self.frame_count = frame_number
        
        # If no detections, mark existing tracks as disappeared
        if not detections:
            # Mark all tracks as disappeared
            for track_id in list(self.tracks.keys()):
                self.tracks[track_id]['disappeared'] += 1
                if self.tracks[track_id]['disappeared'] >= self.max_disappeared:
                    del self.tracks[track_id]
            
            return []
        
        # If no existing tracks, create new tracks for all detections
        if not self.tracks:
            for i, detection in enumerate(detections):
                track_id = f"track_{self.next_track_id}"
                self.next_track_id += 1
                self.tracks[track_id] = {
                    'track_id': track_id,
                    'box': detection.get('box', (0, 0, 0, 0)),
                    'student_id': None,
                    'disappeared': 0,
                    'confidence': detection.get('confidence', 0),
                    'last_seen': frame_number,
                    'frames_verified': 0,
                }
            return [self._format_track(track_id) for track_id in self.tracks]
        
        # Match detections to existing tracks
        used_detection_indices = set()
        matched_tracks = set()
        
        for track_id, track in self.tracks.items():
            best_match_idx = None
            best_iou = 0
            
            for i, detection in enumerate(detections):
                if i in used_detection_indices:
                    continue
                
                detection_box = detection.get('box', (0, 0, 0, 0))
                iou = self._compute_iou(track['box'], detection_box)
                
                if iou > best_iou and iou > self.max_distance:
                    best_iou = iou
                    best_match_idx = i
            
            if best_match_idx is not None:
                # Update existing track
                used_detection_indices.add(best_match_idx)
                matched_tracks.add(track_id)
                detection = detections[best_match_idx]
                
                self.tracks[track_id]['box'] = detection.get('box', track['box'])
                self.tracks[track_id]['disappeared'] = 0
                self.tracks[track_id]['confidence'] = detection.get('confidence', 0)
                self.tracks[track_id]['last_seen'] = frame_number
                
                # If track has student_id, preserve it; otherwise mark as unknown
                if self.tracks[track_id].get('student_id'):
                    self.tracks[track_id]['frames_verified'] += 1
            else:
                # No match found, mark as disappeared
                self.tracks[track_id]['disappeared'] += 1
                if self.tracks[track_id]['disappeared'] >= self.max_disappeared:
                    del self.tracks[track_id]
        
        # Create new tracks for unmatched detections
        for i, detection in enumerate(detections):
            if i not in used_detection_indices:
                track_id = f"track_{self.next_track_id}"
                self.next_track_id += 1
                self.tracks[track_id] = {
                    'track_id': track_id,
                    'box': detection.get('box', (0, 0, 0, 0)),
                    'student_id': None,
                    'disappeared': 0,
                    'confidence': detection.get('confidence', 0),
                    'last_seen': frame_number,
                    'frames_verified': 0,
                }
        
        return [self._format_track(track_id) for track_id in self.tracks]
    
    def _format_track(self, track_id: TrackID) -> dict:
        """Format track data for output.
        
        Args:
            track_id: The tracking ID
            
        Returns:
            Formatted track dictionary
        """
        if track_id not in self.tracks:
            return {}
        
        track = self.tracks[track_id]
        return {
            'track_id': track_id,
            'student_id': track.get('student_id'),
            'box': track['box'],
            'confidence': track['confidence'],
            'last_seen': track['last_seen'],
            'frames_verified': track['frames_verified'],
        }
    
    def get_tracked_face(self, track_id: TrackID) -> Optional[dict]:
        """Get tracked face information by track ID.
        
        Args:
            track_id: The tracking ID
            
        Returns:
            Tracked face data or None if not found
        """
        if track_id in self.tracks:
            track = self.tracks[track_id]
            return {
                'track_id': track_id,
                'student_id': track.get('student_id'),
                'box': track['box'],
                'confidence': track['confidence'],
                'last_seen': track['last_seen'],
                'frames_verified': track['frames_verified'],
            }
        return None