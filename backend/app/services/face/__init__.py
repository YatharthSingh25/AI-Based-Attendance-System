"""Face detection and recognition services."""

from app.services.face.recognizer import (
    DEFAULT_MATCH_THRESHOLD,
    FACE_SIZE,
    MAX_ENROLL_IMAGES,
    MAX_IMAGE_BYTES,
    FaceError,
    build_model,
    confidence_from_distance,
    decode_image,
    decode_sample,
    detect_faces,
    dump_samples,
    encode_sample,
    extract_enrollment_face,
    load_samples,
    recognize,
)

__all__ = [
    "DEFAULT_MATCH_THRESHOLD",
    "FACE_SIZE",
    "MAX_ENROLL_IMAGES",
    "MAX_IMAGE_BYTES",
    "FaceError",
    "build_model",
    "confidence_from_distance",
    "decode_image",
    "decode_sample",
    "detect_faces",
    "dump_samples",
    "encode_sample",
    "extract_enrollment_face",
    "load_samples",
    "recognize",
]
