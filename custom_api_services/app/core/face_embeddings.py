"""
Face embedding extraction and comparison using InsightFace
"""
import cv2
import numpy as np
import os
from typing import Optional, Tuple, Dict, Any, List
from app.models.face_models import get_face_app
from app.core.face_alignment import align_face, align_face_simple
from app.config import EMPLOYEE_FACES_DIR, MAX_EMBEDDINGS_PER_EMPLOYEE, COSINE_THRESHOLD, EMPLOYEE_EMBEDDINGS_DIR

def get_face_embedding(image: np.ndarray, face_coords: Optional[tuple] = None) -> Optional[np.ndarray]:
    """Compute a 512-dim normalized embedding using InsightFace. Returns None if unavailable/failure.

    If face_coords provided, crop to ROI first to help the detector; otherwise run on full image.
    """
    app = get_face_app()
    if app is None:
        print("InsightFace model not available - cannot extract embeddings")
        return None
    try:
        roi_img = image
        if face_coords is not None:
            x, y, w, h = face_coords
            roi_img = image[y:y+h, x:x+w]
        faces = app.get(roi_img)
        if not faces:
            # As a fallback, try full image if we initially cropped
            if roi_img is not image:
                faces = app.get(image)
                if not faces:
                    return None
            else:
                return None
        # Choose face with largest bbox
        face_obj = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        emb = face_obj.normed_embedding
        if emb is None:
            return None
        emb = np.asarray(emb, dtype=np.float32)
        # Ensure L2 normalization
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb
    except Exception as e:
        print(f"Error computing embedding: {str(e)}")
        return None

def extract_face_embedding_enhanced(image: np.ndarray, face_info: tuple) -> Optional[np.ndarray]:
    """Enhanced embedding extraction with standard workflow"""
    try:
        print(f"Starting enhanced embedding extraction with face_info: {face_info[:4]}")
        
        # Use InsightFace to extract embedding
        app = get_face_app()
        if app is None:
            print("InsightFace không khả dụng, fallback to old method")
            return None
        
        # Validate input image
        if image is None or image.size == 0:
            print("Input image is None or empty")
            return None
            
        if len(face_info) < 4:
            print(f"Invalid face_info: {face_info}")
            return None
        
        # Try 1: Face alignment with contour-based extraction
        try:
            # Use face segmentation if InsightFace object is available
            if len(face_info) > 4 and face_info[4] is not None:
                aligned_face = extract_face_with_segmentation(image, face_info[4], face_info[:4])
                print(f"Face extracted with segmentation: {aligned_face.shape}")
            else:
                aligned_face = align_face(image, face_info)
                print(f"Face aligned (standard): {aligned_face.shape}")
            
            # Convert to BGR for InsightFace if needed
            if aligned_face.max() <= 1.0:
                bgr_face = (aligned_face * 255).astype(np.uint8)
            else:
                bgr_face = aligned_face.astype(np.uint8)
                
            if len(bgr_face.shape) == 3 and bgr_face.shape[2] == 3:
                # Check if it's RGB
                if np.mean(bgr_face[:, :, 0]) < np.mean(bgr_face[:, :, 2]):  # R < B suggests RGB
                    bgr_face = cv2.cvtColor(bgr_face, cv2.COLOR_RGB2BGR)
            
            # Extract embedding from aligned face
            faces = app.get(bgr_face)
            
            if faces:
                # Choose face with largest bbox
                face_obj = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                
                # Get normalized embedding
                embedding = face_obj.normed_embedding
                if embedding is not None:
                    # Ensure embedding is normalized to unit length
                    embedding = np.asarray(embedding, dtype=np.float32)
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    
                    print(f"Enhanced embedding extracted successfully: shape={embedding.shape}, norm={np.linalg.norm(embedding):.3f}")
                    return embedding
        except Exception as align_error:
            print(f"Face alignment failed: {str(align_error)}")
        
        # Try 2: Simple direct extraction from original image
        try:
            x, y, w, h = face_info[:4]
            
            # Convert image to BGR uint8 if needed
            if image.max() <= 1.0:
                bgr_image = (image * 255).astype(np.uint8)
            else:
                bgr_image = image.astype(np.uint8)
            
            # Ensure BGR format for InsightFace
            if len(bgr_image.shape) == 3 and bgr_image.shape[2] == 3:
                if np.mean(bgr_image[:, :, 0]) < np.mean(bgr_image[:, :, 2]):
                    bgr_image = cv2.cvtColor(bgr_image, cv2.COLOR_RGB2BGR)
            
            print(f"Processing image: shape={bgr_image.shape}, dtype={bgr_image.dtype}, max={bgr_image.max()}")
            
            # Try direct detection on full image first
            faces = app.get(bgr_image)
            print(f"Direct detection found {len(faces)} faces")
            
            if faces:
                # Choose face with largest bbox
                face_obj_new = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                embedding = face_obj_new.normed_embedding
                if embedding is not None:
                    embedding = np.asarray(embedding, dtype=np.float32)
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    print(f"Direct embedding extracted: shape={embedding.shape}, norm={np.linalg.norm(embedding):.3f}")
                    return embedding
            
            # Fallback: regular crop with margin
            margin = 0.2  # Increased margin for better context
            x_margin = int(w * margin)
            y_margin = int(h * margin)
            x1 = max(0, x - x_margin)
            y1 = max(0, y - y_margin)
            x2 = min(bgr_image.shape[1], x + w + x_margin)
            y2 = min(bgr_image.shape[0], y + h + y_margin)
            
            face_crop = bgr_image[y1:y2, x1:x2]
            print(f"Face cropped (fallback): {face_crop.shape}")
            
            # Validate crop size
            if face_crop.shape[0] < 50 or face_crop.shape[1] < 50:
                print(f"Face crop too small: {face_crop.shape}")
                return None
            
            faces = app.get(face_crop)
            print(f"Cropped detection found {len(faces)} faces")
            
            if faces:
                face_obj_new = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                embedding = face_obj_new.normed_embedding
                if embedding is not None:
                    embedding = np.asarray(embedding, dtype=np.float32)
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    print(f"Fallback embedding extracted: shape={embedding.shape}, norm={np.linalg.norm(embedding):.3f}")
                    return embedding
        except Exception as segmentation_error:
            print(f"Face segmentation method failed: {str(segmentation_error)}")
        
        print("All enhanced embedding methods failed")
        return None
        
    except Exception as e:
        print(f"Lỗi trích xuất embedding enhanced: {str(e)}")
        return None

def extract_face_with_segmentation(image: np.ndarray, face_obj, bbox: tuple) -> np.ndarray:
    """Extract face with segmentation (placeholder - implement if needed)"""
    # For now, use simple alignment
    return align_face_simple(image, bbox)

def compare_embeddings_enhanced(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Compare similarity using standard cosine similarity"""
    try:
        # Ensure embeddings are normalized
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            print("Embedding có norm = 0")
            return -1.0
        
        emb1_normalized = embedding1 / norm1
        emb2_normalized = embedding2 / norm2
        
        # Calculate cosine similarity
        cosine_sim = float(np.dot(emb1_normalized, emb2_normalized))
        
        # Clamp to range [-1, 1] for safety
        cosine_sim = np.clip(cosine_sim, -1.0, 1.0)
        
        print(f"Cosine similarity: {cosine_sim:.4f}")
        return cosine_sim
        
    except Exception as e:
        print(f"Lỗi so sánh embeddings: {str(e)}")
        return -1.0

def make_face_decision(similarity: float, threshold: float = COSINE_THRESHOLD) -> tuple:
    """Make decision based on threshold"""
    try:
        is_same_person = similarity >= threshold
        
        if is_same_person:
            confidence = similarity
            message = f"Cùng người (similarity: {similarity:.3f} >= {threshold})"
        else:
            confidence = similarity
            message = f"Khác người (similarity: {similarity:.3f} < {threshold})"
        
        print(f"Decision: {message}")
        return is_same_person, confidence, message
        
    except Exception as e:
        print(f"Lỗi ra quyết định: {str(e)}")
        return False, 0.0, f"Lỗi: {str(e)}"

# Path helper for stored embeddings
def _employee_embedding_path(employee_id: int) -> str:
    return os.path.join(EMPLOYEE_EMBEDDINGS_DIR, f"employee_{employee_id}_embedding_0.npy")

def save_multiple_employee_embeddings(employee_id: int, embeddings: List[np.ndarray]) -> bool:
    """Save multiple embeddings for an employee (augmented enrollment)"""
    try:
        embeddings_dir = os.path.join(os.getcwd(), EMPLOYEE_EMBEDDINGS_DIR)
        os.makedirs(embeddings_dir, exist_ok=True)
        
        # Clean up old embeddings first
        cleanup_old_embeddings(employee_id, embeddings_dir)
        
        # Save as multiple files
        for i, embedding in enumerate(embeddings):
            filename = f"employee_{employee_id}_embedding_{i}.npy"
            filepath = os.path.join(embeddings_dir, filename)
            np.save(filepath, embedding)
        
        print(f"Saved {len(embeddings)} embeddings for employee {employee_id} to {embeddings_dir}")
        return True
    except Exception as e:
        print(f"Error saving multiple embeddings: {str(e)}")
        return False

def cleanup_old_embeddings(employee_id: int, embeddings_dir: str) -> None:
    """Clean up old embedding files for an employee"""
    try:
        import glob
        pattern = os.path.join(embeddings_dir, f"employee_{employee_id}_embedding_*.npy")
        old_files = glob.glob(pattern)
        for file_path in old_files:
            os.remove(file_path)
        if old_files:
            print(f"Cleaned up {len(old_files)} old embedding files for employee {employee_id}")
    except Exception as e:
        print(f"Error cleaning up old embeddings: {str(e)}")

def save_employee_embedding(employee_id: int, embedding: np.ndarray) -> bool:
    """Save single embedding to employee_embeddings directory (for regular registration)"""
    try:
        embeddings_dir = os.path.join(os.getcwd(), EMPLOYEE_EMBEDDINGS_DIR)
        os.makedirs(embeddings_dir, exist_ok=True)
        
        # Save as single embedding file (index 0)
        filename = f"employee_{employee_id}_embedding_0.npy"
        filepath = os.path.join(embeddings_dir, filename)
        
        # Clean up any existing embeddings first
        cleanup_old_embeddings(employee_id, embeddings_dir)
        
        # Save the single embedding
        np.save(filepath, embedding)
        print(f"Saved single embedding for employee {employee_id} to {embeddings_dir}")
        return True
        
    except Exception as e:
        print(f"Error saving embedding for employee {employee_id}: {str(e)}")
        return False

def load_employee_embeddings(employee_id: int) -> Optional[List[np.ndarray]]:
    """Load multiple embeddings for an employee (augmented enrollment)"""
    try:
        embeddings_dir = os.path.join(os.getcwd(), EMPLOYEE_EMBEDDINGS_DIR)
        embeddings = []
        
        # Look for multiple embedding files
        i = 0
        while True:
            filename = f"employee_{employee_id}_embedding_{i}.npy"
            filepath = os.path.join(embeddings_dir, filename)
            
            if os.path.exists(filepath):
                embedding = np.load(filepath)
                embeddings.append(embedding)
                i += 1
            else:
                break
        
        if len(embeddings) > 0:
            print(f"Loaded {len(embeddings)} embeddings for employee {employee_id}")
            return embeddings
        
        # Fallback to old single embedding format
        old_path = _employee_embedding_path(employee_id)
        if os.path.exists(old_path):
            old_embeddings = np.load(old_path)
            if old_embeddings.ndim == 1:
                embeddings = [old_embeddings]
            elif old_embeddings.ndim == 2:
                embeddings = [old_embeddings[i] for i in range(old_embeddings.shape[0])]
            
            print(f"Loaded {len(embeddings)} embeddings from old format for employee {employee_id}")
            return embeddings
        
        print(f"No embeddings found for employee {employee_id}")
        return None
        
    except Exception as e:
        print(f"Error loading embeddings for employee {employee_id}: {str(e)}")
        return None
