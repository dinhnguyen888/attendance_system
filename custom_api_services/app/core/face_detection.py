"""
Face detection utilities using InsightFace and OpenCV
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
from app.models.face_models import get_face_app
from app.config import *

def detect_faces_insightface(image: np.ndarray) -> List[Tuple]:
    """Detect faces using InsightFace RetinaFace"""
    try:
        app = get_face_app()
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
            # Check if it's RGB (values in [0,1])
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
