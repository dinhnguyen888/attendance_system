"""
Face comparison service for complete face recognition workflow
"""
import numpy as np
from typing import Dict
from services.image_processing_service import preprocess_image
from services.face_detection_service import detect_faces_insightface
from services.embedding_service import extract_face_embedding_enhanced, compare_embeddings_enhanced
from models.config import COSINE_THRESHOLD

def make_face_decision(similarity: float, threshold: float = 0.80) -> tuple:
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

def compare_faces_complete_workflow(image1: np.ndarray, image2: np.ndarray) -> Dict:
    """Complete workflow for comparing 2 faces according to InsightFace + OpenCV standards"""
    try:
        print("=== BẮT ĐẦU QUY TRÌNH SO SÁNH KHUÔN MẶT ===")
        
        # Step 2: Preprocess images
        print("Bước 2: Tiền xử lý ảnh...")
        _, processed_img1 = preprocess_image(image1)
        _, processed_img2 = preprocess_image(image2)
        
        # Step 3: Detect faces
        print("Bước 3: Phát hiện khuôn mặt...")
        faces1 = detect_faces_insightface(processed_img1)
        faces2 = detect_faces_insightface(processed_img2)
        
        if len(faces1) == 0:
            return {"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh 1", "similarity": -1.0}
        
        if len(faces2) == 0:
            return {"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh 2", "similarity": -1.0}
        
        # Choose largest face from each image
        face1_info = max(faces1, key=lambda f: f[2] * f[3])  # w * h
        face2_info = max(faces2, key=lambda f: f[2] * f[3])
        
        # Step 5: Extract features
        print("Bước 5: Trích xuất đặc trưng...")
        embedding1 = extract_face_embedding_enhanced(processed_img1, face1_info)
        embedding2 = extract_face_embedding_enhanced(processed_img2, face2_info)
        
        if embedding1 is None:
            return {"success": False, "message": "Không thể trích xuất embedding từ ảnh 1", "similarity": -1.0}
        
        if embedding2 is None:
            return {"success": False, "message": "Không thể trích xuất embedding từ ảnh 2", "similarity": -1.0}
        
        # Step 6: Compare similarity
        print("Bước 6: So sánh độ tương đồng...")
        similarity = compare_embeddings_enhanced(embedding1, embedding2)
        
        # Step 7: Make decision
        print("Bước 7: Ra quyết định...")
        is_same, confidence, message = make_face_decision(similarity, COSINE_THRESHOLD)
        
        print("=== KẾT THÚC QUY TRÌNH SO SÁNH ===")
        
        return {
            "success": True,
            "is_same_person": is_same,
            "similarity": similarity,
            "confidence": confidence,
            "message": message,
            "threshold": COSINE_THRESHOLD
        }
        
    except Exception as e:
        print(f"Lỗi trong quy trình so sánh: {str(e)}")
        return {"success": False, "message": f"Lỗi: {str(e)}", "similarity": -1.0}
