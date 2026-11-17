"""Face enrollment and recognition for classroom photos.

Uses OpenCV only: a Haar cascade detects frontal faces and an LBPH
recogniser matches them against enrolled samples. Both ship inside
``opencv-contrib-python-headless``, so there is no model download and no
extra native build step at deploy time.

LBPH compares texture, not identity embeddings. It works well when the
enrolled photos and the attendance photo are frontal and reasonably lit,
and it is deliberately conservative: a face farther than the match
threshold is reported as unknown instead of being guessed.
"""

import base64
import json
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np

# Enrolled faces are stored as square, contrast-normalised grayscale crops.
FACE_SIZE = 160

# Lower distance means a closer match. Distances above this are treated as
# unknown faces. Tuned so an unenrolled person is rejected while the same
# person under mild lighting/scale changes still matches.
DEFAULT_MATCH_THRESHOLD = 72.0

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_ENROLL_IMAGES = 8

# Detection is slower on large photos and gains nothing, so shrink first.
MAX_DETECT_DIMENSION = 1000

_CASCADE: Optional[cv2.CascadeClassifier] = None


class FaceError(Exception):
    """Raised when an image cannot be turned into a usable face sample."""


def _cascade() -> cv2.CascadeClassifier:
    global _CASCADE
    if _CASCADE is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(path)
        if cascade.empty():
            raise FaceError("Face detector could not be loaded on the server.")
        _CASCADE = cascade
    return _CASCADE


def decode_image(data: bytes) -> np.ndarray:
    """Decode raw bytes into a BGR image, or raise ``FaceError``."""
    if not data:
        raise FaceError("The uploaded file is empty.")
    buffer = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise FaceError("The uploaded file is not a readable image.")
    return image


def _downscale(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    longest = max(height, width)
    if longest <= MAX_DETECT_DIMENSION:
        return image
    scale = MAX_DETECT_DIMENSION / float(longest)
    return cv2.resize(image, (int(width * scale), int(height * scale)))


def detect_faces(image: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """Return bounding boxes of frontal faces, largest first."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    boxes = _cascade().detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(50, 50),
    )
    found = [tuple(int(value) for value in box) for box in boxes]
    found.sort(key=lambda box: box[2] * box[3], reverse=True)
    return found


def _crop(image: np.ndarray, box: Tuple[int, int, int, int]) -> np.ndarray:
    x, y, width, height = box
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face = gray[y : y + height, x : x + width]
    face = cv2.resize(face, (FACE_SIZE, FACE_SIZE))
    return cv2.equalizeHist(face)


def extract_enrollment_face(data: bytes, filename: str = "") -> np.ndarray:
    """Extract exactly one face from an enrollment photo."""
    image = _downscale(decode_image(data))
    boxes = detect_faces(image)
    label = filename or "image"

    if not boxes:
        raise FaceError(f"{label}: no face was found.")
    if len(boxes) > 1:
        raise FaceError(
            f"{label}: {len(boxes)} faces were found. Enrollment photos must show one person."
        )
    return _crop(image, boxes[0])


def encode_sample(face: np.ndarray) -> str:
    """Serialise one learned face crop for storage."""
    ok, buffer = cv2.imencode(".png", face)
    if not ok:
        raise FaceError("Could not encode the face sample.")
    return base64.b64encode(buffer.tobytes()).decode("ascii")


def decode_sample(text: str) -> np.ndarray:
    raw = base64.b64decode(text)
    buffer = np.frombuffer(raw, np.uint8)
    face = cv2.imdecode(buffer, cv2.IMREAD_GRAYSCALE)
    if face is None:
        raise FaceError("A stored face sample could not be read.")
    if face.shape != (FACE_SIZE, FACE_SIZE):
        face = cv2.resize(face, (FACE_SIZE, FACE_SIZE))
    return face


def dump_samples(samples: Sequence[str]) -> str:
    return json.dumps({"version": 1, "samples": list(samples)})


def load_samples(payload: Optional[str]) -> List[np.ndarray]:
    """Read stored samples, tolerating old placeholder rows."""
    if not payload:
        return []
    try:
        parsed = json.loads(payload)
    except (TypeError, ValueError):
        return []

    if not isinstance(parsed, dict):
        return []

    faces: List[np.ndarray] = []
    for item in parsed.get("samples") or []:
        try:
            faces.append(decode_sample(item))
        except (FaceError, ValueError):
            continue
    return faces


def build_model(
    samples_by_label: Dict[int, Sequence[np.ndarray]]
) -> Optional[Tuple[object, List[int]]]:
    """Train an LBPH model over every enrolled sample."""
    images: List[np.ndarray] = []
    labels: List[int] = []

    for label, samples in samples_by_label.items():
        for sample in samples:
            images.append(sample)
            labels.append(int(label))

    if not images:
        return None

    model = cv2.face.LBPHFaceRecognizer_create()
    model.train(images, np.array(labels, dtype=np.int32))
    return model, sorted(set(labels))


def confidence_from_distance(distance: float) -> float:
    """Map an LBPH distance to a friendly 0-100 score."""
    return round(max(0.0, min(100.0, 100.0 - (distance / 2.0))), 1)


def recognize(
    image_bytes: bytes,
    samples_by_student: Dict[int, Sequence[np.ndarray]],
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> dict:
    """Detect every face in a photo and match it to enrolled students.

    Returns one entry per detected face plus the best match per student.
    """
    image = _downscale(decode_image(image_bytes))
    boxes = detect_faces(image)

    result = {
        "faces_detected": len(boxes),
        "matches": [],
        "unknown_faces": 0,
    }

    if not boxes:
        return result

    built = build_model(samples_by_student)
    if built is None:
        result["unknown_faces"] = len(boxes)
        return result

    model, _labels = built

    best_by_student: Dict[int, Tuple[float, float]] = {}
    for box in boxes:
        crop = _crop(image, box)
        label, distance = model.predict(crop)
        distance = float(distance)

        if distance > threshold:
            result["unknown_faces"] += 1
            continue

        previous = best_by_student.get(int(label))
        if previous is None or distance < previous[0]:
            best_by_student[int(label)] = (distance, confidence_from_distance(distance))

    result["matches"] = [
        {
            "student_id": student_id,
            "distance": round(distance, 1),
            "confidence": confidence,
        }
        for student_id, (distance, confidence) in sorted(
            best_by_student.items(), key=lambda item: item[1][0]
        )
    ]
    return result
