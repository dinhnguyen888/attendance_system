"""Model initialization and singleton access."""
import logging
import os
import threading
from typing import Optional

os.environ["INSIGHTFACE_USE_TORCH"] = os.getenv("INSIGHTFACE_USE_TORCH", "0")
os.environ["ONNXRUNTIME_FORCE_CPU"] = os.getenv("ONNXRUNTIME_FORCE_CPU", "1")

INSIGHTFACE_MODEL = os.getenv("INSIGHTFACE_MODEL", "buffalo_l")
INSIGHTFACE_PROVIDER = os.getenv("INSIGHTFACE_PROVIDER", "CPUExecutionProvider")
INSIGHTFACE_CTX_ID = int(os.getenv("INSIGHTFACE_CTX_ID", "-1"))
INSIGHTFACE_DET_SIZE = int(os.getenv("INSIGHTFACE_DET_SIZE", "640"))

try:
    from insightface.app import FaceAnalysis
    _INSIGHTFACE_AVAILABLE = True
except Exception:
    _INSIGHTFACE_AVAILABLE = False

_face_app = None
_model_lock = threading.Lock()
_yolo_detector = None
_yolo_lock = threading.Lock()
_logger = logging.getLogger(__name__)


def get_face_app() -> Optional["FaceAnalysis"]:
    if not _INSIGHTFACE_AVAILABLE:
        return None

    global _face_app
    if _face_app is None:
        with _model_lock:
            if _face_app is None:
                try:
                    app = FaceAnalysis(name=INSIGHTFACE_MODEL, providers=[INSIGHTFACE_PROVIDER])
                    app.prepare(ctx_id=INSIGHTFACE_CTX_ID, det_size=(INSIGHTFACE_DET_SIZE, INSIGHTFACE_DET_SIZE))
                    _face_app = app
                except Exception as exc:
                    _logger.error("INSIGHTFACE_INIT_FAILED: %s", exc)
                    return None
    return _face_app


def is_insightface_available() -> bool:
    return _INSIGHTFACE_AVAILABLE


def get_yolo_detector():
    global _yolo_detector
    if _yolo_detector is None:
        with _yolo_lock:
            if _yolo_detector is None:
                try:
                    from app.inference.yolo_detector import YOLOv11DeviceDetector
                    _yolo_detector = YOLOv11DeviceDetector()
                except Exception as exc:
                    _logger.error("YOLO_INIT_FAILED: %s", exc)
                    _yolo_detector = None
    return _yolo_detector
