"""
Face recognition service - high-level business logic
"""
import numpy as np
from typing import Dict, Any
from app.core.image_processing import process_uploaded_image, preprocess_image
from app.core.face_detection import detect_faces_insightface
from app.core.skin_normalization import normalize_skin_tone
from app.core.canny_features import (
    extract_canny_feature_points, 
    compare_canny_features,
    save_employee_canny_features,
    load_employee_canny_features
)
from app.core.face_embeddings import (
    extract_face_embedding_enhanced,
    compare_embeddings_enhanced,
    make_face_decision
)
from app.core.validation import validate_image_aspect_ratio, validate_background_color
from app.core.file_operations import save_employee_face, delete_employee_files
from app.core.image_processing import extract_face_region_only
from app.config import CANNY_THRESHOLD, COSINE_THRESHOLD

class FaceRecognitionService:
    """Main service for face recognition operations"""
    
    def register_employee_face(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        """Register employee face with validation and feature extraction"""
        try:
            print(f"Processing registration for employee {employee_id}, action: {action}")
            
            # Process uploaded image
            image = process_uploaded_image(face_image_file)
            
            # Validate image aspect ratio
            aspect_valid, aspect_msg = validate_image_aspect_ratio(image)
            if not aspect_valid:
                return {
                    "success": False,
                    "message": f"Tỉ lệ khung hình không hợp lệ: {aspect_msg}"
                }
            
            # Validate background color
            bg_valid, bg_msg = validate_background_color(image)
            if not bg_valid:
                return {
                    "success": False,
                    "message": f"Màu nền không hợp lệ: {bg_msg}"
                }
            
            print(f"Image validation passed: {aspect_msg}, {bg_msg}")
            
            # Detect faces directly on original image (no resize)
            faces = detect_faces_insightface(image)
            
            if len(faces) == 0:
                return {
                    "success": False,
                    "message": "Không tìm thấy khuôn mặt trong ảnh"
                }
            
            if len(faces) > 1:
                return {
                    "success": False,
                    "message": "Phát hiện nhiều khuôn mặt. Vui lòng chụp ảnh chỉ có một khuôn mặt",
                    "confidence": 0.0
                }
            
            # Apply skin tone normalization before feature extraction
            face_info = faces[0]
            face_obj = face_info[4] if len(face_info) > 4 else None
            
            # Normalize skin tone on original image
            normalized_image = normalize_skin_tone(image, face_info[:4], face_obj)
            
            # Extract Canny feature points from normalized image
            canny_features = extract_canny_feature_points(normalized_image, face_obj, face_info[:4])
            
            if canny_features is None:
                return {
                    "success": False,
                    "message": "Không thể trích xuất đặc trưng khuôn mặt từ ảnh"
                }
            
            # Save Canny feature points
            save_employee_canny_features(employee_id, canny_features)
            
            # Crop and save only face region from original image (not resized)
            face_region = extract_face_region_only(image, face_info[:4], margin_ratio=0.05)
            save_employee_face(employee_id, face_region)
            
            return {
                "success": True, 
                "message": f"Đăng ký khuôn mặt thành công cho nhân viên {employee_id}",
                "employee_id": employee_id,
                "confidence": 1.0
            }
            
        except Exception as e:
            print(f"Error in register_employee_face: {str(e)}")
            return {
                "success": False,
                "message": f"Lỗi xử lý: {str(e)}",
                "confidence": 0.0,
                "employee_id": None
            }
    
    def verify_employee_face(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        """Verify employee face for check-in/check-out"""
        try:
            print(f"Processing verification for employee {employee_id}, action: {action}")
            
            # Process uploaded image
            image = process_uploaded_image(face_image_file)
            
            # Preprocess and detect faces according to standard workflow
            _, processed_image = preprocess_image(image)
            faces = detect_faces_insightface(processed_image)
            
            if len(faces) == 0:
                return {
                    "success": False,
                    "message": "Không tìm thấy khuôn mặt trong ảnh",
                    "confidence": 0.0,
                    "employee_id": employee_id
                }
            
            if len(faces) > 1:
                return {
                    "success": False,
                    "message": "Phát hiện nhiều khuôn mặt. Vui lòng chụp ảnh chỉ có một khuôn mặt",
                    "confidence": 0.0,
                    "employee_id": employee_id
                }
            
            # Apply skin tone normalization before feature extraction
            face_info = faces[0]
            face_obj = face_info[4] if len(face_info) > 4 else None
            
            # Normalize skin tone on original image (not processed_image)
            normalized_image = normalize_skin_tone(image, face_info[:4], face_obj)
            
            # Preprocess normalized image
            _, normalized_processed_image = preprocess_image(normalized_image)
            
            # Extract Canny feature points from normalized image
            current_features = extract_canny_feature_points(normalized_processed_image, face_obj, face_info[:4])
            
            # Check if employee has registered Canny features
            stored_features = load_employee_canny_features(employee_id)
            
            if stored_features is None:
                return {
                    "success": False,
                    "message": "Nhân viên chưa đăng ký khuôn mặt. Vui lòng đăng ký trước",
                    "confidence": 0.0,
                    "employee_id": employee_id
                }
            
            # Compare Canny feature points
            similarity = compare_canny_features(current_features, stored_features, threshold=0.1)
            
            print(f"Canny feature comparison — similarity: {similarity:.3f}")
            
            if similarity >= CANNY_THRESHOLD:
                return {
                    "success": True,
                    "message": f"{action.capitalize()} thành công",
                    "confidence": similarity,
                    "employee_id": employee_id
                }
            else:
                return {
                    "success": False,
                    "message": f"Khuôn mặt không khớp với nhân viên (similarity: {similarity:.3f})",
                    "confidence": similarity,
                    "employee_id": employee_id
                }
                
        except Exception as e:
            print(f"Error in verify_employee_face: {str(e)}")
            return {
                "success": False,
                "message": f"Lỗi xử lý: {str(e)}",
                "confidence": 0.0,
                "employee_id": employee_id
            }
    
    def compare_two_faces(self, face_image1_file, face_image2_file) -> Dict[str, Any]:
        """Compare two faces using complete workflow"""
        try:
            print("=== TESTING COMPLETE FACE COMPARISON WORKFLOW ===")
            
            # Process both uploaded images
            image1 = process_uploaded_image(face_image1_file)
            image2 = process_uploaded_image(face_image2_file)
            
            # Run complete comparison workflow
            result = self._compare_faces_complete_workflow(image1, image2)
            
            return result
            
        except Exception as e:
            print(f"Error in compare_two_faces: {str(e)}")
            return {
                "success": False,
                "message": f"Lỗi xử lý: {str(e)}",
                "similarity": -1.0
            }
    
    def delete_employee_data(self, employee_id: int) -> Dict[str, Any]:
        """Delete all employee face data"""
        try:
            result = delete_employee_files(employee_id)
            
            if not result["deleted_files"] and not result["errors"]:
                return {
                    "success": False,
                    "message": f"Không tìm thấy dữ liệu cho nhân viên {employee_id}",
                    "employee_id": employee_id,
                    "deleted_files": [],
                    "errors": []
                }
            
            success = len(result["errors"]) == 0
            message = f"Đã xóa thành công dữ liệu cho nhân viên {employee_id}" if success else f"Xóa một phần dữ liệu cho nhân viên {employee_id}"
            
            return {
                "success": success,
                "message": message,
                "employee_id": employee_id,
                "deleted_files": result["deleted_files"],
                "errors": result["errors"]
            }
            
        except Exception as e:
            print(f"Error in delete_employee_data: {str(e)}")
            return {
                "success": False,
                "message": f"Lỗi khi xóa dữ liệu nhân viên: {str(e)}",
                "employee_id": employee_id,
                "deleted_files": [],
                "errors": [str(e)]
            }
    
    def _compare_faces_complete_workflow(self, image1: np.ndarray, image2: np.ndarray) -> Dict[str, Any]:
        """Complete workflow for comparing 2 faces according to InsightFace + OpenCV standards"""
        try:
            print("=== BẮT ĐẦU QUY TRÌNH SO SÁNH KHUÔN MẶT ===")
            
            # Step 2: Image preprocessing
            print("Bước 2: Tiền xử lý ảnh...")
            _, processed_img1 = preprocess_image(image1)
            _, processed_img2 = preprocess_image(image2)
            
            # Step 3: Face detection
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
            
            # Step 5: Feature extraction
            print("Bước 5: Trích xuất đặc trưng...")
            embedding1 = extract_face_embedding_enhanced(processed_img1, face1_info)
            embedding2 = extract_face_embedding_enhanced(processed_img2, face2_info)
            
            if embedding1 is None:
                return {"success": False, "message": "Không thể trích xuất embedding từ ảnh 1", "similarity": -1.0}
            
            if embedding2 is None:
                return {"success": False, "message": "Không thể trích xuất embedding từ ảnh 2", "similarity": -1.0}
            
            # Step 6: Similarity comparison
            print("Bước 6: So sánh độ tương đồng...")
            similarity = compare_embeddings_enhanced(embedding1, embedding2)
            
            # Step 7: Decision making
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
