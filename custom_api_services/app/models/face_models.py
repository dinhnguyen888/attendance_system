"""
Face recognition model initialization and management
"""
import threading
from typing import Optional
import numpy as np
from app.config import *

try:
    from insightface.app import FaceAnalysis
    _INSIGHTFACE_AVAILABLE = True
except Exception as _e:
    print(f"InsightFace not available: {_e}")
    _INSIGHTFACE_AVAILABLE = False

# Global model instance and thread lock
_face_app = None
_model_lock = threading.Lock()

def get_face_app() -> Optional["FaceAnalysis"]:
    """Get or initialize the InsightFace model (thread-safe)"""
    if not _INSIGHTFACE_AVAILABLE:
        return None
    
    global _face_app
    if _face_app is None:
        with _model_lock:
            if _face_app is None:
                app = FaceAnalysis(name="buffalo_l")
                # CPU mode: ctx_id=-1
                app.prepare(ctx_id=-1, det_size=TARGET_SIZE)
                _face_app = app
    return _face_app

def is_insightface_available() -> bool:
    """Check if InsightFace is available"""
    return _INSIGHTFACE_AVAILABLE
