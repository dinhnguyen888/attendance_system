"""Stateless face detection, alignment, embedding, and comparison."""
import os
from typing import Optional

import cv2
import numpy as np

STANDARD_FACE_SIZE_VALUE = int(os.getenv("STANDARD_FACE_SIZE", "112"))
STANDARD_FACE_SIZE = (STANDARD_FACE_SIZE_VALUE, STANDARD_FACE_SIZE_VALUE)
MIN_FACE_SIZE = (int(os.getenv("MIN_FACE_WIDTH", "80")), int(os.getenv("MIN_FACE_HEIGHT", "80")))
SCALE_FACTOR = float(os.getenv("SCALE_FACTOR", "1.05"))
MIN_NEIGHBORS = int(os.getenv("MIN_NEIGHBORS", "6"))
FACE_CROP_MARGIN = float(os.getenv("FACE_CROP_MARGIN", "0.15"))
from app.inference.models import get_face_app


def detect_faces(image: np.ndarray):
    app = get_face_app()
    if app is not None:
        try:
            faces = []
            for face in app.get(image):
                x, y, x2, y2 = face.bbox.astype(int)
                faces.append((x, y, x2 - x, y2 - y, face))
            return faces
        except Exception:
            pass
    return _detect_faces_opencv(image)


def extract_embedding(image: np.ndarray, face_info: tuple) -> Optional[np.ndarray]:
    app = get_face_app()
    if app is None or image is None or image.size == 0:
        return None

    for candidate in (_align_face(image, face_info), _as_bgr_uint8(image), _crop_face(image, face_info)):
        if candidate is None:
            continue
        try:
            faces = app.get(candidate)
            if not faces:
                continue
            face = max(faces, key=lambda item: (item.bbox[2] - item.bbox[0]) * (item.bbox[3] - item.bbox[1]))
            embedding = normalize_embedding(face.normed_embedding)
            if embedding is not None:
                return embedding
        except Exception:
            pass
    return None


def compare_embeddings(left: np.ndarray, right: np.ndarray) -> float:
    left = normalize_embedding(left)
    right = normalize_embedding(right)
    if left is None or right is None:
        return -1.0
    return float(np.clip(np.dot(left, right), -1.0, 1.0))


def normalize_embedding(embedding) -> Optional[np.ndarray]:
    if embedding is None:
        return None
    embedding = np.asarray(embedding, dtype=np.float32)
    norm = np.linalg.norm(embedding)
    return None if norm <= 0 else embedding / norm


def _detect_faces_opencv(image: np.ndarray):
    try:
        bgr = _as_bgr_uint8(image)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=SCALE_FACTOR,
            minNeighbors=MIN_NEIGHBORS,
            minSize=MIN_FACE_SIZE,
            flags=cv2.CASCADE_SCALE_IMAGE,
        )
        return [(x, y, w, h, None) for x, y, w, h in faces]
    except Exception:
        return []


def _align_face(image: np.ndarray, face_info: tuple) -> Optional[np.ndarray]:
    try:
        x, y, w, h, face = face_info
        if face is None or getattr(face, "kps", None) is None:
            return _resize_face(image, (x, y, w, h))
        landmarks = face.kps.astype(np.float32)
        standard = np.array([
            [38.2946, 51.6963],
            [73.5318, 51.5014],
            [56.0252, 71.7366],
            [41.5493, 92.3655],
            [70.7299, 92.2041],
        ], dtype=np.float32)
        transform = cv2.estimateAffinePartial2D(landmarks, standard)[0]
        return _as_bgr_uint8(cv2.warpAffine(image, transform, STANDARD_FACE_SIZE))
    except Exception:
        return _crop_face(image, face_info)


def _crop_face(image: np.ndarray, face_info: tuple) -> Optional[np.ndarray]:
    try:
        return _resize_face(image, face_info[:4], margin=0.2)
    except Exception:
        return None


def _resize_face(image: np.ndarray, face_box: tuple, margin: float = FACE_CROP_MARGIN) -> np.ndarray:
    x, y, w, h = face_box
    x_margin = int(w * margin)
    y_margin = int(h * margin)
    x1 = max(0, x - x_margin)
    y1 = max(0, y - y_margin)
    x2 = min(image.shape[1], x + w + x_margin)
    y2 = min(image.shape[0], y + h + y_margin)
    crop = image[y1:y2, x1:x2]
    if crop.shape[0] < 50 or crop.shape[1] < 50:
        return None
    return _as_bgr_uint8(cv2.resize(crop, STANDARD_FACE_SIZE, interpolation=cv2.INTER_LINEAR))


def _as_bgr_uint8(image: np.ndarray) -> np.ndarray:
    prepared = (image * 255).astype(np.uint8) if image.max() <= 1.0 else image.astype(np.uint8)
    if len(prepared.shape) == 3 and prepared.shape[2] == 3:
        if np.mean(prepared[:, :, 0]) < np.mean(prepared[:, :, 2]):
            return cv2.cvtColor(prepared, cv2.COLOR_RGB2BGR)
    return prepared
