"""
File storage service for face recognition API
"""
import cv2
import numpy as np
import os
from typing import Optional
from models.config import *

def save_employee_face(employee_id: int, face_image: np.ndarray):
    """Save employee's face image"""
    try:
        # Ensure directory exists
        if not os.path.exists(EMPLOYEE_FACES_DIR):
            os.makedirs(EMPLOYEE_FACES_DIR, exist_ok=True)
        
        # Create file path
        face_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}.jpg")
        
        # Save image
        success = cv2.imwrite(face_path, face_image)
        if not success:
            raise ValueError("Không thể lưu ảnh khuôn mặt")
        
        print(f"Đã lưu ảnh khuôn mặt cho employee {employee_id} tại {face_path}")
        
    except Exception as e:
        print(f"Lỗi khi lưu ảnh khuôn mặt cho employee {employee_id}: {str(e)}")
        raise

def load_employee_face(employee_id: int) -> Optional[np.ndarray]:
    """Load employee's face image"""
    face_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}.jpg")
    if os.path.exists(face_path):
        return cv2.imread(face_path)
    return None

def delete_employee_files(employee_id: int) -> tuple:
    """Delete all files related to an employee"""
    deleted_files = []
    errors = []
    
    # Delete face image
    face_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}.jpg")
    if os.path.exists(face_path):
        try:
            os.remove(face_path)
            deleted_files.append(f"employee_{employee_id}.jpg")
            print(f"Deleted face image: {face_path}")
        except Exception as e:
            errors.append(f"Cannot delete face image: {str(e)}")
    
    # Delete Canny features
    features_path = os.path.join(EMPLOYEE_CANNY_FEATURES_DIR, f"employee_{employee_id}_features.npy")
    if os.path.exists(features_path):
        try:
            os.remove(features_path)
            deleted_files.append(f"employee_{employee_id}_features.npy")
            print(f"Deleted Canny features: {features_path}")
        except Exception as e:
            errors.append(f"Cannot delete Canny features: {str(e)}")
    
    # Delete embedding (legacy - can be removed later)
    from services.embedding_service import _employee_embedding_path
    embedding_path = _employee_embedding_path(employee_id)
    if os.path.exists(embedding_path):
        try:
            os.remove(embedding_path)
            deleted_files.append(f"employee_{employee_id}.npy")
            print(f"Deleted embedding: {embedding_path}")
        except Exception as e:
            errors.append(f"Cannot delete embedding: {str(e)}")
    
    return deleted_files, errors

def count_employee_faces() -> int:
    """Count number of employee face images"""
    try:
        return len([f for f in os.listdir(EMPLOYEE_FACES_DIR) if f.endswith('.jpg')])
    except:
        return 0

def count_embeddings() -> tuple:
    """Count embedding files and total samples"""
    try:
        emb_files = [f for f in os.listdir(EMPLOYEE_FACES_DIR) if f.endswith('.npy')]
        total_samples = 0
        for f in emb_files:
            try:
                arr = np.load(os.path.join(EMPLOYEE_FACES_DIR, f))
                if arr.ndim == 1:
                    total_samples += 1
                elif arr.ndim == 2:
                    total_samples += int(arr.shape[0])
            except Exception:
                pass
        return len(emb_files), total_samples
    except:
        return 0, 0
