"""
Verification service: encapsulates employee face verification workflows.
"""
from typing import Dict, Any
from app.core.image_processing import preprocess_image
from app.core.face_detection import detect_faces_insightface
from app.core.skin_normalization import normalize_skin_tone
from app.core.canny_features import (
    extract_canny_feature_points,
    compare_canny_features,
    load_employee_canny_features,
)
from app.core.face_embeddings import (
    extract_face_embedding_enhanced,
    compare_embeddings_enhanced,
    load_employee_embeddings,
)


class VerificationService:
    def verify_employee_face_max_similarity(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        try:
            import numpy as np
            import cv2
            from app.core.enrollment_pipeline import verify_with_max_similarity

            image_array = np.frombuffer(face_image_file.read(), np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if image is None:
                return {"success": False, "message": "Không thể đọc file ảnh"}

            result = verify_with_max_similarity(employee_id, image)
            return result
        except Exception as e:
            print(f"Error in max similarity verification: {str(e)}")
            return {"success": False, "message": f"Lỗi xác thực: {str(e)}"}

    def verify_employee_face(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        try:
            from app.core.image_processing import process_uploaded_image
            from app.core.anti_spoofing_verifier import AntiSpoofingVerifier
            from app.core.lbp_orb_features import extract_lbp_orb_combined, compare_lbp_orb_combined
            from app.core.file_operations import load_employee_lbp_orb_features
            from app.config import HIGH_CONFIDENCE_THRESHOLD, LOW_CONFIDENCE_THRESHOLD

            image = process_uploaded_image(face_image_file)

            anti_spoofing = AntiSpoofingVerifier()
            spoofing_result = anti_spoofing.verify_no_device_spoofing(image)
            if spoofing_result['spoofing_detected']:
                spoofing_device = spoofing_result.get('spoofing_device', 'unknown device')
                message = f"⚠️ PHÁT HIỆN GIAN LẬN: Khuôn mặt được hiển thị qua {spoofing_device}. Vui lòng chụp ảnh trực tiếp."
                return {
                    "success": False,
                    "message": message,
                    "confidence": 0.0,
                    "employee_id": employee_id,
                    "spoofing_detected": True,
                    "spoofing_type": spoofing_result.get('spoofing_type', 'device_presentation_attack'),
                    "spoofing_device": spoofing_device,
                    "anti_spoofing_details": spoofing_result
                }

            _, processed_image = preprocess_image(image)
            faces = detect_faces_insightface(processed_image, select_closest=True)
            if len(faces) == 0:
                return {"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh", "confidence": 0.0, "employee_id": employee_id}

            face_info = faces[0]
            face_obj = face_info[4] if len(face_info) > 4 else None
            normalized_image = normalize_skin_tone(image, face_info[:4], face_obj)

            current_arcface = extract_face_embedding_enhanced(normalized_image, face_info)
            if current_arcface is None:
                try:
                    x, y, w, h = face_info[:4]
                    face_crop = normalized_image[y:y + h, x:x + w]
                    from app.core.face_embeddings import get_face_embedding
                    current_arcface = get_face_embedding(face_crop)
                except Exception:
                    current_arcface = None

            current_lbp_orb = extract_lbp_orb_combined(normalized_image, face_info[:4])
            stored_arcface = load_employee_embeddings(employee_id)
            stored_lbp_orb = load_employee_lbp_orb_features(employee_id)

            arcface_similarity = 0.0
            lbp_orb_similarity = 0.0
            final_confidence = 0.0
            comparison_method = "No Method Available"

            if current_arcface is not None and stored_arcface is not None and len(stored_arcface) > 0:
                arcface_similarity = compare_embeddings_enhanced(current_arcface, stored_arcface[0])
                from app.config import ARCFACE_THRESHOLD
                if arcface_similarity >= HIGH_CONFIDENCE_THRESHOLD:
                    final_confidence = arcface_similarity
                    comparison_method = "ArcFace (High Confidence)"
                else:
                    comparison_method = "ArcFace"
                    final_confidence = arcface_similarity

            if current_lbp_orb is not None and stored_lbp_orb is not None:
                lbp_orb_similarity = compare_lbp_orb_combined(current_lbp_orb, stored_lbp_orb)
                if comparison_method == "ArcFace":
                    final_confidence = 0.7 * arcface_similarity + 0.3 * lbp_orb_similarity
                    comparison_method = "ArcFace + LBP+ORB"
                elif comparison_method == "No Method Available":
                    final_confidence = lbp_orb_similarity
                    comparison_method = "LBP+ORB Only"

            if final_confidence < LOW_CONFIDENCE_THRESHOLD and comparison_method != "No Method Available":
                pass

            _, normalized_processed_image = preprocess_image(normalized_image)
            current_features = extract_canny_feature_points(normalized_processed_image, face_obj, face_info[:4])
            stored_features = load_employee_canny_features(employee_id)

            canny_similarity = 0.0
            canny_available = False
            if current_features is not None and stored_features is not None:
                canny_similarity = compare_canny_features(current_features, stored_features, threshold=0.1)
                canny_available = True

            if comparison_method == "No Method Available":
                if canny_available:
                    final_confidence = canny_similarity
                    comparison_method = "Canny Only"
                else:
                    pass
            else:
                if canny_available:
                    combined_confidence = 0.85 * final_confidence + 0.15 * canny_similarity
                    final_confidence = combined_confidence
                    comparison_method += " + Canny"
                else:
                    final_confidence *= 0.95
                    comparison_method += " (No Canny)"

            if comparison_method == "No Method Available":
                return {
                    "success": False,
                    "message": "Nhân viên chưa đăng ký khuôn mặt hoặc không thể trích xuất đặc trưng. Vui lòng đăng ký lại",
                    "confidence": 0.0,
                    "employee_id": employee_id
                }

            from app.config import LBP_ORB_THRESHOLD, CANNY_THRESHOLD
            if "ArcFace" in comparison_method:
                from app.config import ARCFACE_THRESHOLD
                threshold = ARCFACE_THRESHOLD
            elif "LBP+ORB" in comparison_method:
                threshold = LBP_ORB_THRESHOLD
            else:
                threshold = CANNY_THRESHOLD

            if final_confidence >= threshold:
                return {"success": True, "message": f"{action.capitalize()} thành công ({comparison_method})", "employee_id": employee_id}
            else:
                return {"success": False, "message": f"Khuôn mặt không khớp với nhân viên ({comparison_method} similarity: {final_confidence:.3f})", "confidence": final_confidence, "employee_id": employee_id}
        except Exception as e:
            print(f"Error in verify_employee_face: {str(e)}")
            return {"success": False, "message": f"Lỗi xử lý: {str(e)}", "confidence": 0.0, "employee_id": employee_id}


