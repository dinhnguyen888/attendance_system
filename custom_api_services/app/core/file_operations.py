"""
File operations for face data storage and retrieval
"""
import cv2
import numpy as np
import os
from typing import Optional
from app.config import EMPLOYEE_FACES_DIR

def save_employee_lbp_orb_features(employee_id: int, features: dict):
    """Save LBP+ORB features for employee"""
    try:
        if not os.path.exists(EMPLOYEE_FACES_DIR):
            os.makedirs(EMPLOYEE_FACES_DIR, exist_ok=True)
        
        features_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}_lbp_orb.npy")
        np.save(features_path, features)
        print(f"LBP+ORB features saved for employee {employee_id}")
        
    except Exception as e:
        print(f"Error saving LBP+ORB features for employee {employee_id}: {str(e)}")

def load_employee_lbp_orb_features(employee_id: int) -> Optional[dict]:
    """Load LBP+ORB features for employee"""
    try:
        features_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}_lbp_orb.npy")
        if os.path.exists(features_path):
            features = np.load(features_path, allow_pickle=True).item()
            return features
        return None
    except Exception as e:
        print(f"Error loading LBP+ORB features for employee {employee_id}: {str(e)}")
        return None

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

def delete_employee_files(employee_id: int) -> dict:
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
    from app.config import EMPLOYEE_CANNY_FEATURES_DIR
    features_path = os.path.join(EMPLOYEE_CANNY_FEATURES_DIR, f"employee_{employee_id}_features.npy")
    if os.path.exists(features_path):
        try:
            os.remove(features_path)
            deleted_files.append(f"employee_{employee_id}_features.npy")
            print(f"Deleted Canny features: {features_path}")
        except Exception as e:
            errors.append(f"Cannot delete Canny features: {str(e)}")
    
    # Delete ArcFace embedding
    from app.core.face_embeddings import _employee_embedding_path
    embedding_path = _employee_embedding_path(employee_id)
    if os.path.exists(embedding_path):
        try:
            os.remove(embedding_path)
            deleted_files.append(f"employee_{employee_id}_embedding_0.npy")
            print(f"Deleted ArcFace embedding: {embedding_path}")
        except Exception as e:
            errors.append(f"Cannot delete ArcFace embedding: {str(e)}")
    
    # Delete LBP+ORB features
    lbp_orb_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}_lbp_orb.npy")
    if os.path.exists(lbp_orb_path):
        try:
            os.remove(lbp_orb_path)
            deleted_files.append(f"employee_{employee_id}_lbp_orb.npy")
            print(f"Deleted LBP+ORB features: {lbp_orb_path}")
        except Exception as e:
            errors.append(f"Cannot delete LBP+ORB features: {str(e)}")
    
    return {
        "deleted_files": deleted_files,
        "errors": errors
    }
