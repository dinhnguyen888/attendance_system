"""
Face alignment utilities using facial landmarks
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from app.config import STANDARD_FACE_SIZE

def align_face(image: np.ndarray, face_info: tuple) -> np.ndarray:
    """Align face using facial landmarks"""
    try:
        x, y, w, h, face_obj = face_info
        
        # If we have InsightFace face object with landmarks
        if face_obj is not None and hasattr(face_obj, 'kps') and face_obj.kps is not None:
            # Use landmarks from InsightFace for alignment
            landmarks = face_obj.kps.astype(np.float32)
            
            # Define standard landmarks for 112x112 face
            standard_landmarks = np.array([
                [38.2946, 51.6963],  # Left eye
                [73.5318, 51.5014],  # Right eye  
                [56.0252, 71.7366],  # Nose tip
                [41.5493, 92.3655],  # Left mouth corner
                [70.7299, 92.2041]   # Right mouth corner
            ], dtype=np.float32)
            
            # Calculate affine transformation matrix
            tform = cv2.estimateAffinePartial2D(landmarks, standard_landmarks)[0]
            
            # Apply transformation
            aligned_face = cv2.warpAffine(image, tform, STANDARD_FACE_SIZE)
            
            print("Face aligned using InsightFace landmarks")
            return aligned_face
        
        else:
            # Fallback: Simple crop and resize
            return align_face_simple(image, (x, y, w, h))
            
    except Exception as e:
        print(f"Lỗi căn chỉnh khuôn mặt: {str(e)}")
        # Fallback to simple alignment
        x, y, w, h = face_info[:4]
        return align_face_simple(image, (x, y, w, h))

def align_face_simple(image: np.ndarray, face_coords: tuple) -> np.ndarray:
    """Simple face alignment by crop and resize"""
    try:
        x, y, w, h = face_coords
        
        # Expand face region by 15% for better context (reduced from 20%)
        margin = 0.15
        x_margin = int(w * margin)
        y_margin = int(h * margin)
        
        # Calculate expanded region
        x1 = max(0, x - x_margin)
        y1 = max(0, y - y_margin)
        x2 = min(image.shape[1], x + w + x_margin)
        y2 = min(image.shape[0], y + h + y_margin)
        
        # Crop face with margin
        face_roi = image[y1:y2, x1:x2]
        
        # Resize to standard 112x112 for InsightFace
        aligned_face = cv2.resize(face_roi, STANDARD_FACE_SIZE, interpolation=cv2.INTER_LINEAR)
        
        print(f"Face aligned (simple): {face_roi.shape} -> {aligned_face.shape}")
        return aligned_face
        
    except Exception as e:
        print(f"Lỗi căn chỉnh khuôn mặt đơn giản: {str(e)}")
        raise
