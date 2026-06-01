"""Image/video decoding helpers."""
from io import BytesIO
import os

import av
import cv2
import numpy as np

MAX_ANALYZE_FRAMES = int(os.getenv("MAX_ANALYZE_FRAMES", "7"))
PHOTO_ASPECT_RATIO = float(os.getenv("PHOTO_ASPECT_RATIO", "0.75"))
PHOTO_ASPECT_RATIO_TOLERANCE = float(os.getenv("PHOTO_ASPECT_RATIO_TOLERANCE", "0.08"))
PHOTO_BACKGROUND_MIN_COVERAGE = float(os.getenv("PHOTO_BACKGROUND_MIN_COVERAGE", "0.55"))


def decode_image(image_bytes: bytes):
    if not image_bytes:
        return None
    return cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)


def sample_video_frames(video_bytes: bytes, max_frames: int = MAX_ANALYZE_FRAMES):
    max_frames = max(1, min(max_frames or MAX_ANALYZE_FRAMES, MAX_ANALYZE_FRAMES))
    with av.open(BytesIO(video_bytes)) as container:
        frames = [
            (index, cv2.cvtColor(frame.to_ndarray(format="rgb24"), cv2.COLOR_RGB2BGR))
            for index, frame in enumerate(container.decode(video=0))
        ]
    if len(frames) <= max_frames:
        return frames
    indices = np.linspace(0, len(frames) - 1, num=max_frames, dtype=int)
    return [frames[int(index)] for index in indices]


def face_quality(image: np.ndarray, face_info):
    x, y, w, h = face_info[:4]
    face = image[max(0, y):max(0, y) + h, max(0, x):max(0, x) + w]
    if face.size == 0:
        return {"blur_score": 0.0, "brightness_score": 0.0}
    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    return {
        "blur_score": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        "brightness_score": float(np.mean(gray) / 255.0),
    }


def portrait_photo_quality(image: np.ndarray, face_info):
    height, width = image.shape[:2]
    aspect_ratio = float(width / height) if height else 0.0
    aspect_ratio_ok = bool(abs(aspect_ratio - PHOTO_ASPECT_RATIO) <= PHOTO_ASPECT_RATIO_TOLERANCE)
    background = _background_color_metrics(image, face_info)
    return {
        "image_width": int(width),
        "image_height": int(height),
        "aspect_ratio": aspect_ratio,
        "expected_aspect_ratio": PHOTO_ASPECT_RATIO,
        "aspect_ratio_tolerance": PHOTO_ASPECT_RATIO_TOLERANCE,
        "aspect_ratio_ok": aspect_ratio_ok,
        **background,
    }


def _background_color_metrics(image: np.ndarray, face_info):
    background = _background_pixels(image, face_info)
    if background.size == 0:
        return {
            "background_ok": False,
            "background_color": "UNKNOWN",
            "background_allowed_coverage": 0.0,
            "background_white_coverage": 0.0,
            "background_blue_coverage": 0.0,
            "background_min_coverage": PHOTO_BACKGROUND_MIN_COVERAGE,
        }

    hsv = cv2.cvtColor(background.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
    hue = hsv[:, 0]
    saturation = hsv[:, 1] / 255.0
    value = hsv[:, 2] / 255.0
    white_mask = (saturation <= 0.25) & (value >= 0.70)
    blue_mask = (hue >= 85) & (hue <= 135) & (saturation >= 0.20) & (value >= 0.25)
    white_coverage = float(np.mean(white_mask))
    blue_coverage = float(np.mean(blue_mask))
    allowed_coverage = float(np.mean(white_mask | blue_mask))
    dominant_color = "WHITE" if white_coverage >= blue_coverage else "BLUE"
    return {
        "background_ok": bool(allowed_coverage >= PHOTO_BACKGROUND_MIN_COVERAGE),
        "background_color": dominant_color,
        "background_allowed_coverage": allowed_coverage,
        "background_white_coverage": white_coverage,
        "background_blue_coverage": blue_coverage,
        "background_min_coverage": PHOTO_BACKGROUND_MIN_COVERAGE,
    }


def _background_pixels(image: np.ndarray, face_info):
    height, width = image.shape[:2]
    x, y, w, h = face_info[:4]
    pad_x = int(w * 0.20)
    pad_y = int(h * 0.25)
    x1 = max(0, int(x - pad_x))
    y1 = max(0, int(y - pad_y))
    x2 = min(width, int(x + w + pad_x))
    y2 = min(height, int(y + h + pad_y))
    mask = np.ones((height, width), dtype=bool)
    mask[y1:y2, x1:x2] = False
    return image[mask]
