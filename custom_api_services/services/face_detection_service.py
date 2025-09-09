"""
Face detection service using InsightFace and OpenCV
"""
import cv2
import numpy as np
from typing import Optional, List, Tuple
import insightface
from insightface.app import FaceAnalysis
import threading
from models.config import *

# InsightFace availability check
try:
    from insightface.app import FaceAnalysis
    _INSIGHTFACE_AVAILABLE = True
except Exception as _e:
    print(f"InsightFace not available: {_e}")
    _INSIGHTFACE_AVAILABLE = False

# Lazy global model for embeddings
_face_app = None
_model_lock = threading.Lock()

def _get_face_app() -> Optional["FaceAnalysis"]:
    """Get or initialize the InsightFace model"""
    if not _INSIGHTFACE_AVAILABLE:
        return None
    global _face_app
    if _face_app is None:
        with _model_lock:
            if _face_app is None:
                app = FaceAnalysis(name="buffalo_l")
                # CPU mode: ctx_id=-1
                app.prepare(ctx_id=-1, det_size=DETECTION_SIZE)
                _face_app = app
    return _face_app

def detect_faces_insightface(image: np.ndarray) -> List[Tuple]:
    """Detect faces using InsightFace RetinaFace"""
    try:
        app = _get_face_app()
        if app is None:
            # Fallback to OpenCV Haar cascades
            return detect_faces_opencv(image)
        
        # Use InsightFace to detect faces
        faces = app.get(image)
        
        if not faces:
            print("Không tìm thấy khuôn mặt bằng InsightFace")
            return []
        
        # Convert format from InsightFace to OpenCV format (x, y, w, h)
        opencv_faces = []
        for face in faces:
            bbox = face.bbox.astype(int)
            x, y, x2, y2 = bbox
            w, h = x2 - x, y2 - y
            opencv_faces.append((x, y, w, h, face))  # Add face object for landmarks
        
        print(f"InsightFace detected {len(opencv_faces)} faces")
        return opencv_faces
        
    except Exception as e:
        print(f"Lỗi phát hiện khuôn mặt InsightFace: {str(e)}")
        # Fallback to OpenCV
        return detect_faces_opencv(image)

def detect_faces_opencv(image: np.ndarray) -> List[Tuple]:
    """Fallback: Detect faces using OpenCV Haar cascades"""
    try:
        # Convert to BGR if needed for OpenCV
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Check if RGB (values in [0,1])
            if image.max() <= 1.0:
                bgr_image = (image * 255).astype(np.uint8)
                bgr_image = cv2.cvtColor(bgr_image, cv2.COLOR_RGB2BGR)
            else:
                bgr_image = image
        else:
            bgr_image = image
        
        # Load cascade classifier with optimal parameters
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces with optimal parameters
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=SCALE_FACTOR,
            minNeighbors=MIN_NEIGHBORS,
            minSize=MIN_FACE_SIZE,
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Convert format for compatibility
        opencv_faces = [(x, y, w, h, None) for x, y, w, h in faces]
        
        print(f"OpenCV detected {len(opencv_faces)} faces")
        return opencv_faces
        
    except Exception as e:
        print(f"Lỗi phát hiện khuôn mặt OpenCV: {str(e)}")
        return []
