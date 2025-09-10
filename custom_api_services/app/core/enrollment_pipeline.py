"""
Enhanced enrollment pipeline for 3x4 photos with augmentation
"""
import cv2
import numpy as np
from typing import List, Optional, Dict, Any
from app.core.augmentation import generate_augmented_faces, assess_face_quality
from app.core.face_embeddings import extract_face_embedding_enhanced
from app.core.face_detection import detect_faces_insightface
from app.core.face_alignment import align_face
from app.core.skin_normalization import normalize_skin_tone

def enroll_employee_from_3x4(employee_id: int, image_3x4: np.ndarray) -> Dict[str, Any]:
    """
    Enhanced enrollment from 3x4 photo with augmentation
    
    Steps:
    1. Detect face in 3x4 photo
    2. Align face using landmarks
    3. Generate augmented variations (rotation, lighting, blur)
    4. Extract embeddings for all variations
    5. Save multiple embeddings as employee profile
    """
    try:
        print(f"Starting enhanced enrollment for employee {employee_id}")
        
        # Step 1: Face detection
        faces = detect_faces_insightface(image_3x4)
        if len(faces) == 0:
            return {
                "success": False,
                "message": "Không tìm thấy khuôn mặt trong ảnh 3x4",
                "embeddings_count": 0
            }
        
        if len(faces) > 1:
            return {
                "success": False,
                "message": "Phát hiện nhiều khuôn mặt trong ảnh 3x4. Vui lòng sử dụng ảnh chỉ có một khuôn mặt",
                "embeddings_count": 0
            }
        
        face_info = faces[0]
        face_obj = face_info[4] if len(face_info) > 4 else None
        
        # Step 2: Face alignment and normalization
        aligned_face = align_face(image_3x4, face_info)
        normalized_face = normalize_skin_tone(aligned_face, face_info[:4], face_obj)
        
        # Step 3: Quality assessment
        quality_score, quality_metrics = assess_face_quality(normalized_face)
        print(f"Face quality score: {quality_score:.3f}")
        
        if quality_score < 0.4:
            return {
                "success": False,
                "message": f"Chất lượng ảnh quá thấp (score: {quality_score:.3f}). Vui lòng sử dụng ảnh chất lượng tốt hơn",
                "quality_score": quality_score,
                "embeddings_count": 0
            }
        
        # Step 4: Generate augmented variations
        augmented_faces = generate_augmented_faces(normalized_face, num_augmentations=8)
        print(f"Generated {len(augmented_faces)} augmented variations")
        
        # Step 5: Extract embeddings for all variations
        embeddings = []
        successful_extractions = 0
        
        for i, aug_face in enumerate(augmented_faces):
            try:
                # Create face_info for augmented face
                h, w = aug_face.shape[:2]
                aug_face_info = (0, 0, w, h, face_obj)
                
                embedding = extract_face_embedding_enhanced(aug_face, aug_face_info)
                if embedding is not None:
                    embeddings.append(embedding)
                    successful_extractions += 1
                    print(f"Embedding {i+1}/{len(augmented_faces)} extracted successfully")
                else:
                    print(f"Failed to extract embedding {i+1}/{len(augmented_faces)}")
            except Exception as e:
                print(f"Error extracting embedding {i+1}: {str(e)}")
        
        if len(embeddings) == 0:
            return {
                "success": False,
                "message": "Không thể trích xuất embedding từ bất kỳ biến thể nào",
                "embeddings_count": 0
            }
        
        # Step 6: Save multiple embeddings
        from app.core.face_embeddings import save_multiple_employee_embeddings
        save_multiple_employee_embeddings(employee_id, embeddings)
        
        # Step 7: Save original face image
        from app.core.file_operations import save_employee_face
        face_region = extract_face_region_from_aligned(aligned_face)
        save_employee_face(employee_id, face_region)
        
        return {
            "success": True,
            "message": f"Đăng ký thành công với {len(embeddings)} embeddings từ ảnh 3x4",
            "employee_id": employee_id,
            "embeddings_count": len(embeddings),
            "quality_score": quality_score,
            "quality_metrics": quality_metrics
        }
        
    except Exception as e:
        print(f"Error in enhanced enrollment: {str(e)}")
        return {
            "success": False,
            "message": f"Lỗi trong quá trình đăng ký: {str(e)}",
            "embeddings_count": 0
        }

def extract_face_region_from_aligned(aligned_face: np.ndarray) -> np.ndarray:
    """Extract face region from aligned face image"""
    try:
        # Aligned face is already cropped, just return it
        return aligned_face
    except Exception as e:
        print(f"Error extracting face region: {str(e)}")
        return aligned_face

def verify_with_max_similarity(employee_id: int, webcam_frame: np.ndarray) -> Dict[str, Any]:
    """
    Verify webcam frame against multiple stored embeddings using max similarity
    
    Steps:
    1. Preprocess webcam frame
    2. Extract embedding from webcam
    3. Load all stored embeddings for employee
    4. Calculate similarity with all stored embeddings
    5. Use max similarity for decision
    """
    try:
        from app.core.augmentation import preprocess_webcam_frame
        from app.core.face_embeddings import load_employee_embeddings, compare_embeddings_enhanced
        
        print(f"Starting max similarity verification for employee {employee_id}")
        
        # Step 1: Preprocess webcam frame
        processed_frame, quality_score, quality_metrics = preprocess_webcam_frame(webcam_frame)
        
        if quality_score < 0.3:
            return {
                "success": False,
                "message": f"Chất lượng ảnh webcam quá thấp (score: {quality_score:.3f}). Vui lòng chụp lại",
                "quality_score": quality_score,
                "confidence": 0.0
            }
        
        # Step 2: Face detection and alignment
        faces = detect_faces_insightface(processed_frame)
        if len(faces) == 0:
            return {
                "success": False,
                "message": "Không tìm thấy khuôn mặt trong ảnh webcam",
                "confidence": 0.0
            }
        
        if len(faces) > 1:
            return {
                "success": False,
                "message": "Phát hiện nhiều khuôn mặt. Vui lòng đảm bảo chỉ có một khuôn mặt trong khung hình",
                "confidence": 0.0
            }
        
        face_info = faces[0]
        face_obj = face_info[4] if len(face_info) > 4 else None
        
        # Step 3: Extract embedding from webcam
        aligned_webcam = align_face(processed_frame, face_info)
        normalized_webcam = normalize_skin_tone(aligned_webcam, face_info[:4], face_obj)
        
        h, w = normalized_webcam.shape[:2]
        webcam_face_info = (0, 0, w, h, face_obj)
        
        current_embedding = extract_face_embedding_enhanced(normalized_webcam, webcam_face_info)
        if current_embedding is None:
            return {
                "success": False,
                "message": "Không thể trích xuất embedding từ ảnh webcam",
                "confidence": 0.0
            }
        
        # Step 4: Load stored embeddings
        stored_embeddings = load_employee_embeddings(employee_id)
        if stored_embeddings is None or len(stored_embeddings) == 0:
            return {
                "success": False,
                "message": "Nhân viên chưa đăng ký khuôn mặt",
                "confidence": 0.0
            }
        
        # Step 5: Calculate max similarity
        similarities = []
        for i, stored_emb in enumerate(stored_embeddings):
            similarity = compare_embeddings_enhanced(current_embedding, stored_emb)
            similarities.append(similarity)
            print(f"Similarity with embedding {i+1}: {similarity:.4f}")
        
        max_similarity = max(similarities)
        avg_similarity = np.mean(similarities)
        
        # Step 6: Decision based on max similarity
        from app.config import ARCFACE_THRESHOLD
        
        if max_similarity >= ARCFACE_THRESHOLD:
            return {
                "success": True,
                "message": f"Xác thực thành công (max similarity: {max_similarity:.4f})",
                "confidence": max_similarity,
                "max_similarity": max_similarity,
                "avg_similarity": avg_similarity,
                "embeddings_compared": len(similarities),
                "quality_score": quality_score
            }
        else:
            return {
                "success": False,
                "message": f"Khuôn mặt không khớp (max similarity: {max_similarity:.4f} < {ARCFACE_THRESHOLD})",
                "confidence": max_similarity,
                "max_similarity": max_similarity,
                "avg_similarity": avg_similarity,
                "embeddings_compared": len(similarities),
                "quality_score": quality_score
            }
        
    except Exception as e:
        print(f"Error in max similarity verification: {str(e)}")
        return {
            "success": False,
            "message": f"Lỗi trong quá trình xác thực: {str(e)}",
            "confidence": 0.0
        }
