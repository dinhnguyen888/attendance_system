"""
Face recognition model initialization and management
"""
import threading
from typing import Optional
import numpy as np
from app.config import *
import logging

try:
    from insightface.app import FaceAnalysis
    _INSIGHTFACE_AVAILABLE = True
except Exception as _e:
    print(f"InsightFace not available: {_e}")
    _INSIGHTFACE_AVAILABLE = False

# Global model instance and thread lock
_face_app = None
_model_lock = threading.Lock()
_yolo_detector = None
_yolo_lock = threading.Lock()

def get_face_app() -> Optional["FaceAnalysis"]:
    """Get or initialize the InsightFace model with RetinaFace + ArcFace (thread-safe)"""
    if not _INSIGHTFACE_AVAILABLE:
        print("InsightFace not available - returning None")
        return None
    
    global _face_app
    if _face_app is None:
        with _model_lock:
            if _face_app is None:
                try:
                    print("Initializing InsightFace model...")
                    # Use buffalo_l which includes RetinaFace for detection + ArcFace for recognition
                    app = FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
                    # CPU mode: ctx_id=-1, optimized detection size
                    app.prepare(ctx_id=-1, det_size=(640, 640))
                    _face_app = app
                    print("InsightFace initialized successfully with RetinaFace detection + ArcFace recognition")
                except Exception as e:
                    print(f"Failed to initialize InsightFace: {str(e)}")
                    return None
    return _face_app

def is_insightface_available() -> bool:
    """Check if InsightFace is available"""
    return _INSIGHTFACE_AVAILABLE


def get_yolo_detector():
    """Khởi tạo YOLO detector dùng chung (lazy, thread-safe)."""
    global _yolo_detector
    if _yolo_detector is None:
        with _yolo_lock:
            if _yolo_detector is None:
                try:
                    from app.core.yolo_detector import YOLOv11DeviceDetector
                    _yolo_detector = YOLOv11DeviceDetector()
                except Exception as e:
                    logging.getLogger(__name__).error(f"Failed to init YOLO detector: {e}")
                    _yolo_detector = None
    return _yolo_detector
