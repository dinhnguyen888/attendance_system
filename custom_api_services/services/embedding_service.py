"""
Face embedding service using InsightFace for face recognition API
"""
import cv2
import numpy as np
import os
from typing import Optional
from services.face_detection_service import _get_face_app
from services.face_alignment_service import align_face, extract_face_with_segmentation
from models.config import *

def get_face_embedding(image: np.ndarray, face_coords: Optional[tuple] = None) -> Optional[np.ndarray]:
    """Compute a 512-dim normalized embedding using InsightFace"""
    app = _get_face_app()
    if app is None:
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
    """Extract face embedding using enhanced workflow with ArcFace"""
    try:
        print(f"Starting enhanced embedding extraction with face_info: {face_info[:4]}")
        
        # Use InsightFace to extract embedding
        app = _get_face_app()
        if app is None:
            print("InsightFace không khả dụng, fallback to old method")
            return None
        
        # Try 1: Align face with contour-based extraction
        try:
            # Use face segmentation if we have InsightFace object
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
                # Check if RGB
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
        
        # Try 2: Use contour-based extraction directly
        try:
            x, y, w, h = face_info[:4]
            face_obj = face_info[4] if len(face_info) > 4 else None
            
            # Convert image to BGR uint8 if needed
            if image.max() <= 1.0:
                bgr_image = (image * 255).astype(np.uint8)
            else:
                bgr_image = image.astype(np.uint8)
            
            if len(bgr_image.shape) == 3 and bgr_image.shape[2] == 3:
                if np.mean(bgr_image[:, :, 0]) < np.mean(bgr_image[:, :, 2]):
                    bgr_image = cv2.cvtColor(bgr_image, cv2.COLOR_RGB2BGR)
            
            # Use face segmentation if we have face object
            if face_obj is not None:
                segmented_face = extract_face_with_segmentation(bgr_image, face_obj, (x, y, w, h))
                print(f"Segmented face extracted: {segmented_face.shape}")
                
                # Extract embedding from segmented face
                faces = app.get(segmented_face)
                if faces:
                    face_obj_new = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                    embedding = face_obj_new.normed_embedding
                    if embedding is not None:
                        embedding = np.asarray(embedding, dtype=np.float32)
                        norm = np.linalg.norm(embedding)
                        if norm > 0:
                            embedding = embedding / norm
                        print(f"Segmentation embedding extracted: shape={embedding.shape}, norm={np.linalg.norm(embedding):.3f}")
                        return embedding
            
            # Fallback: regular crop
            margin = 0.1
            x_margin = int(w * margin)
            y_margin = int(h * margin)
            x1 = max(0, x - x_margin)
            y1 = max(0, y - y_margin)
            x2 = min(bgr_image.shape[1], x + w + x_margin)
            y2 = min(bgr_image.shape[0], y + h + y_margin)
            
            face_crop = bgr_image[y1:y2, x1:x2]
            print(f"Face cropped (fallback): {face_crop.shape}")
            
            faces = app.get(face_crop)
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
        
        # Clamp to range [-1, 1] to ensure
        cosine_sim = np.clip(cosine_sim, -1.0, 1.0)
        
        print(f"Cosine similarity: {cosine_sim:.4f}")
        return cosine_sim
        
    except Exception as e:
        print(f"Lỗi so sánh embeddings: {str(e)}")
        return -1.0

def save_employee_embedding(employee_id: int, embedding: np.ndarray) -> None:
    """Save employee embedding"""
    try:
        path = _employee_embedding_path(employee_id)
        stacked: Optional[np.ndarray] = None
        if os.path.exists(path):
            try:
                existing = np.load(path)
                if existing.ndim == 1 and existing.shape[0] == embedding.shape[0]:
                    stacked = np.stack([existing, embedding], axis=0)
                elif existing.ndim == 2 and existing.shape[1] == embedding.shape[0]:
                    stacked = np.vstack([existing, embedding[None, :]])
                else:
                    stacked = embedding[None, :]
            except Exception as _e:
                print(f"Không đọc được embeddings cũ cho employee {employee_id}: {_e}")
                stacked = embedding[None, :]
        else:
            stacked = embedding[None, :]

        # Keep maximum N latest embeddings
        if stacked.shape[0] > MAX_EMBEDDINGS_PER_EMPLOYEE:
            stacked = stacked[-MAX_EMBEDDINGS_PER_EMPLOYEE:, :]

        np.save(path, stacked)
    except Exception as e:
        print(f"Lỗi khi lưu embedding cho employee {employee_id}: {str(e)}")

def load_employee_embeddings(employee_id: int) -> Optional[np.ndarray]:
    """Load employee embeddings"""
    try:
        path = _employee_embedding_path(employee_id)
        if not os.path.exists(path):
            return None
        emb = np.load(path)
        # Ensure 2D array (num_samples, 512)
        if emb.ndim == 1:
            emb = emb[None, :]
        # Normalize rows
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        emb = (emb / norms).astype(np.float32)
        return emb
    except Exception as e:
        print(f"Lỗi khi tải embeddings cho employee {employee_id}: {str(e)}")
        return None

def _employee_embedding_path(employee_id: int) -> str:
    """Get path for employee embedding file"""
    return os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}.npy")
