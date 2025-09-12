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
    
    def register_employee_face_augmented(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        """Enhanced registration using augmented enrollment pipeline"""
        try:
            from app.core.enrollment_pipeline import enroll_employee_from_3x4
            
            # Read and validate image
            image_array = np.frombuffer(face_image_file.read(), np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                return {"success": False, "message": "Không thể đọc file ảnh"}
            
            # Use enhanced enrollment pipeline
            result = enroll_employee_from_3x4(employee_id, image)
            return result
            
        except Exception as e:
            print(f"Error in augmented registration: {str(e)}")
            return {"success": False, "message": f"Lỗi đăng ký: {str(e)}"}

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
            
            # Extract ArcFace embedding (primary method)
            arcface_embedding = extract_face_embedding_enhanced(normalized_image, face_info)
            
            if arcface_embedding is None:
                print(f"Primary ArcFace extraction failed for employee {employee_id}")
                # Try simple embedding extraction as fallback
                try:
                    x, y, w, h = face_info[:4]
                    face_crop = normalized_image[y:y+h, x:x+w]
                    from app.core.face_embeddings import get_face_embedding
                    arcface_embedding = get_face_embedding(face_crop)
                    if arcface_embedding is not None:
                        print(f"Fallback ArcFace extraction successful: {arcface_embedding.shape}")
                except Exception as fallback_error:
                    print(f"Fallback ArcFace extraction error: {str(fallback_error)}")
                    arcface_embedding = None
            
            # Extract LBP+ORB features (backup method)
            from app.core.lbp_orb_features import extract_lbp_orb_combined
            from app.core.file_operations import save_employee_lbp_orb_features
            
            lbp_orb_features = extract_lbp_orb_combined(normalized_image, face_info[:4])
            
            # Extract Canny features (auxiliary method - demoted)
            canny_features = extract_canny_feature_points(normalized_image, face_obj, face_info[:4])
            
            # Save all available features
            if arcface_embedding is not None:
                from app.core.face_embeddings import save_employee_embedding
                save_employee_embedding(employee_id, arcface_embedding)
                print(f"ArcFace embedding saved for employee {employee_id}")
            
            if lbp_orb_features is not None:
                save_employee_lbp_orb_features(employee_id, lbp_orb_features)
                print(f"LBP+ORB features saved for employee {employee_id}")
            
            if canny_features is not None:
                save_employee_canny_features(employee_id, canny_features)
                print(f"Canny features saved for employee {employee_id}")
            
            # Check if we have at least one method available
            if arcface_embedding is None and lbp_orb_features is None and canny_features is None:
                return {
                    "success": False,
                    "message": "Không thể trích xuất bất kỳ đặc trưng nào từ khuôn mặt. Vui lòng thử lại với ảnh chất lượng tốt hơn."
                }
            
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
    
    def verify_employee_face_max_similarity(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        """Enhanced verification using max similarity with multiple embeddings"""
        try:
            from app.core.enrollment_pipeline import verify_with_max_similarity
            
            # Read and validate image
            image_array = np.frombuffer(face_image_file.read(), np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                return {"success": False, "message": "Không thể đọc file ảnh"}
            
            # Use enhanced verification pipeline
            result = verify_with_max_similarity(employee_id, image)
            return result
            
        except Exception as e:
            print(f"Error in max similarity verification: {str(e)}")
            return {"success": False, "message": f"Lỗi xác thực: {str(e)}"}

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
            
            # Extract ArcFace embedding (primary method)
            current_arcface = extract_face_embedding_enhanced(normalized_image, face_info)
            
            if current_arcface is None:
                print(f"Primary ArcFace extraction failed for verification of employee {employee_id}")
                # Try simple embedding extraction as fallback
                try:
                    x, y, w, h = face_info[:4]
                    face_crop = normalized_image[y:y+h, x:x+w]
                    from app.core.face_embeddings import get_face_embedding
                    current_arcface = get_face_embedding(face_crop)
                    if current_arcface is not None:
                        print(f"Fallback ArcFace extraction successful for verification")
                except Exception as fallback_error:
                    print(f"Fallback ArcFace extraction error: {str(fallback_error)}")
                    current_arcface = None
            
            # Extract LBP+ORB features (backup method)
            from app.core.lbp_orb_features import extract_lbp_orb_combined, compare_lbp_orb_combined
            from app.core.file_operations import load_employee_lbp_orb_features
            
            current_lbp_orb = extract_lbp_orb_combined(normalized_image, face_info[:4])
            
            # Load stored features
            from app.core.face_embeddings import load_employee_embeddings
            stored_arcface = load_employee_embeddings(employee_id)
            stored_lbp_orb = load_employee_lbp_orb_features(employee_id)
            
            # Initialize scoring variables
            arcface_similarity = 0.0
            lbp_orb_similarity = 0.0
            final_confidence = 0.0
            comparison_method = "No Method Available"
            
            # Primary method: ArcFace comparison
            if current_arcface is not None and stored_arcface is not None and len(stored_arcface) > 0:
                arcface_similarity = compare_embeddings_enhanced(current_arcface, stored_arcface[0])
                print(f"ArcFace comparison — similarity: {arcface_similarity:.3f}")
                
                # Check if ArcFace confidence is high enough to use alone
                from app.config import HIGH_CONFIDENCE_THRESHOLD, ARCFACE_THRESHOLD
                if arcface_similarity >= HIGH_CONFIDENCE_THRESHOLD:
                    final_confidence = arcface_similarity
                    comparison_method = "ArcFace (High Confidence)"
                    print(f"Using ArcFace only (high confidence): {final_confidence:.3f}")
                else:
                    # ArcFace confidence is moderate, check backup methods
                    comparison_method = "ArcFace"
                    final_confidence = arcface_similarity
            
            # Backup method: LBP+ORB comparison (when ArcFace confidence is low or unavailable)
            if current_lbp_orb is not None and stored_lbp_orb is not None:
                lbp_orb_similarity = compare_lbp_orb_combined(current_lbp_orb, stored_lbp_orb)
                print(f"LBP+ORB comparison — similarity: {lbp_orb_similarity:.3f}")
                
                if comparison_method == "ArcFace":
                    # Combine ArcFace + LBP+ORB: 70% ArcFace + 30% LBP+ORB
                    final_confidence = 0.7 * arcface_similarity + 0.3 * lbp_orb_similarity
                    comparison_method = "ArcFace + LBP+ORB"
                    print(f"Combined ArcFace+LBP+ORB confidence: {final_confidence:.3f}")
                elif comparison_method == "No Method Available":
                    # Use LBP+ORB only
                    final_confidence = lbp_orb_similarity
                    comparison_method = "LBP+ORB Only"
                    print(f"Using LBP+ORB only: {final_confidence:.3f}")
            
            # Check if we need to fall back to auxiliary methods
            from app.config import LOW_CONFIDENCE_THRESHOLD
            if final_confidence < LOW_CONFIDENCE_THRESHOLD and comparison_method != "No Method Available":
                print(f"Confidence too low ({final_confidence:.3f}), checking auxiliary methods")
            
            # MANDATORY: Always extract and compare Canny features at the end
            _, normalized_processed_image = preprocess_image(normalized_image)
            current_features = extract_canny_feature_points(normalized_processed_image, face_obj, face_info[:4])
            stored_features = load_employee_canny_features(employee_id)
            
            # Always check Canny features at the end (mandatory step)
            canny_similarity = 0.0
            canny_available = False
            
            if current_features is not None and stored_features is not None:
                canny_similarity = compare_canny_features(current_features, stored_features, threshold=0.1)
                canny_available = True
                print(f"Canny MANDATORY check — similarity: {canny_similarity:.3f}")
            else:
                print("WARNING: Canny features not available - this reduces accuracy")
            
            # Apply Canny combination logic
            if comparison_method == "No Method Available":
                if canny_available:
                    # Use Canny as only method
                    final_confidence = canny_similarity
                    comparison_method = "Canny Only"
                    print(f"Using Canny only: {final_confidence:.3f}")
                else:
                    print("No features available for comparison")
            else:
                # ALWAYS combine with Canny when available - use simpler weighted average
                if canny_available:
                    # Simplified combination: 85% main method + 15% Canny (fixed weights)
                    combined_confidence = 0.85 * final_confidence + 0.15 * canny_similarity
                    weight_info = "85% main + 15% Canny"
                    
                    print(f"MANDATORY Canny combination ({weight_info}): {final_confidence:.3f} + {canny_similarity:.3f} -> {combined_confidence:.3f}")
                    final_confidence = combined_confidence
                    comparison_method += " + Canny"
                else:
                    # Canny features not available - small penalty
                    final_confidence *= 0.95  # 5% penalty for missing Canny
                    print(f"Canny unavailable - applying 5% penalty: {final_confidence:.3f}")
                    comparison_method += " (No Canny)"
            
            # Check if no methods are available
            if comparison_method == "No Method Available":
                return {
                    "success": False,
                    "message": "Nhân viên chưa đăng ký khuôn mặt hoặc không thể trích xuất đặc trưng. Vui lòng đăng ký lại",
                    "confidence": 0.0,
                    "employee_id": employee_id
                }
            
            # Determine appropriate threshold based on comparison method
            if "ArcFace" in comparison_method:
                threshold = ARCFACE_THRESHOLD
            elif "LBP+ORB" in comparison_method:
                from app.config import LBP_ORB_THRESHOLD
                threshold = LBP_ORB_THRESHOLD
            else:
                from app.config import CANNY_THRESHOLD
                threshold = CANNY_THRESHOLD
            if final_confidence >= threshold:
                return {
                    "success": True,
                    "message": f"{action.capitalize()} thành công ({comparison_method})",
                    "confidence": final_confidence,
                    "employee_id": employee_id
                }
            else:
                return {
                    "success": False,
                    "message": f"Khuôn mặt không khớp với nhân viên ({comparison_method} similarity: {final_confidence:.3f})",
                    "confidence": final_confidence,
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
