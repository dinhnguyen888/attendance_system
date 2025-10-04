"""
Registration service: encapsulates employee face registration workflows.
"""
from typing import Dict, Any
import numpy as np
import cv2

from app.core.image_processing import process_uploaded_image
from app.core.face_detection import detect_faces_insightface
from app.core.skin_normalization import normalize_skin_tone
from app.core.canny_features import (
    extract_canny_feature_points,
    save_employee_canny_features,
)
from app.core.face_embeddings import (
    extract_face_embedding_enhanced,
)
from app.core.validation import validate_image_aspect_ratio, validate_background_color
from app.core.file_operations import save_employee_face
from app.core.image_processing import extract_face_region_only


class RegistrationService:
    def register_employee_face_augmented(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        try:
            from app.core.enrollment_pipeline import enroll_employee_from_3x4

            image_array = np.frombuffer(face_image_file.read(), np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if image is None:
                return {"success": False, "message": "Không thể đọc file ảnh"}

            result = enroll_employee_from_3x4(employee_id, image)
            return result
        except Exception as e:
            print(f"Error in augmented registration: {str(e)}")
            return {"success": False, "message": f"Lỗi đăng ký: {str(e)}"}

    def register_employee_face(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        try:
            image = process_uploaded_image(face_image_file)

            aspect_valid, aspect_msg = validate_image_aspect_ratio(image)
            if not aspect_valid:
                return {"success": False, "message": f"Tỉ lệ khung hình không hợp lệ: {aspect_msg}"}

            bg_valid, bg_msg = validate_background_color(image)
            if not bg_valid:
                return {"success": False, "message": f"Màu nền không hợp lệ: {bg_msg}"}

            faces = detect_faces_insightface(image, select_closest=True)
            if len(faces) == 0:
                return {"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh", "confidence": 0.0}

            face_info = faces[0]
            face_obj = face_info[4] if len(face_info) > 4 else None

            normalized_image = normalize_skin_tone(image, face_info[:4], face_obj)

            arcface_embedding = extract_face_embedding_enhanced(normalized_image, face_info)
            if arcface_embedding is None:
                try:
                    x, y, w, h = face_info[:4]
                    face_crop = normalized_image[y:y + h, x:x + w]
                    from app.core.face_embeddings import get_face_embedding
                    arcface_embedding = get_face_embedding(face_crop)
                except Exception:
                    arcface_embedding = None

            from app.core.lbp_orb_features import extract_lbp_orb_combined
            from app.core.file_operations import save_employee_lbp_orb_features

            lbp_orb_features = extract_lbp_orb_combined(normalized_image, face_info[:4])
            canny_features = extract_canny_feature_points(normalized_image, face_obj, face_info[:4])

            if arcface_embedding is not None:
                from app.core.face_embeddings import save_employee_embedding
                save_employee_embedding(employee_id, arcface_embedding)

            if lbp_orb_features is not None:
                save_employee_lbp_orb_features(employee_id, lbp_orb_features)

            if canny_features is not None:
                save_employee_canny_features(employee_id, canny_features)

            if arcface_embedding is None and lbp_orb_features is None and canny_features is None:
                return {"success": False, "message": "Không thể trích xuất bất kỳ đặc trưng nào từ khuôn mặt. Vui lòng thử lại với ảnh chất lượng tốt hơn."}

            face_region = extract_face_region_only(image, face_info[:4], margin_ratio=0.05)
            save_employee_face(employee_id, face_region)

            return {"success": True, "message": f"Đăng ký khuôn mặt thành công cho nhân viên {employee_id}", "employee_id": employee_id, "confidence": 1.0}
        except Exception as e:
            print(f"Error in register_employee_face: {str(e)}")
            return {"success": False, "message": f"Lỗi xử lý: {str(e)}", "confidence": 0.0, "employee_id": None}


