"""
Management service: non-verification operations (compare two faces, delete data).
"""
from typing import Dict, Any
import numpy as np
from app.core.image_processing import preprocess_image
from app.core.face_detection import detect_faces_insightface
from app.core.face_embeddings import (
    extract_face_embedding_enhanced,
    compare_embeddings_enhanced,
)
from app.core.file_operations import delete_employee_files
from app.core.image_processing import process_uploaded_image
from app.config import COSINE_THRESHOLD


class ManagementService:
    def compare_two_faces(self, face_image1_file, face_image2_file) -> Dict[str, Any]:
        try:
            image1 = process_uploaded_image(face_image1_file)
            image2 = process_uploaded_image(face_image2_file)
            return self._compare_faces_complete_workflow(image1, image2)
        except Exception as e:
            print(f"Error in compare_two_faces: {str(e)}")
            return {"success": False, "message": f"Lỗi xử lý: {str(e)}", "similarity": -1.0}

    def delete_employee_data(self, employee_id: int) -> Dict[str, Any]:
        try:
            result = delete_employee_files(employee_id)
            if not result["deleted_files"] and not result["errors"]:
                return {"success": False, "message": f"Không tìm thấy dữ liệu cho nhân viên {employee_id}", "employee_id": employee_id, "deleted_files": [], "errors": []}
            success = len(result["errors"]) == 0
            message = f"Đã xóa thành công dữ liệu cho nhân viên {employee_id}" if success else f"Xóa một phần dữ liệu cho nhân viên {employee_id}"
            return {"success": success, "message": message, "employee_id": employee_id, "deleted_files": result["deleted_files"], "errors": result["errors"]}
        except Exception as e:
            print(f"Error in delete_employee_data: {str(e)}")
            return {"success": False, "message": f"Lỗi khi xóa dữ liệu nhân viên: {str(e)}", "employee_id": employee_id, "deleted_files": [], "errors": [str(e)]}

    def _compare_faces_complete_workflow(self, image1: np.ndarray, image2: np.ndarray) -> Dict[str, Any]:
        try:
            _, processed_img1 = preprocess_image(image1)
            _, processed_img2 = preprocess_image(image2)
            faces1 = detect_faces_insightface(processed_img1, select_closest=True)
            faces2 = detect_faces_insightface(processed_img2, select_closest=True)
            if len(faces1) == 0:
                return {"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh 1", "similarity": -1.0}
            if len(faces2) == 0:
                return {"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh 2", "similarity": -1.0}
            face1_info = max(faces1, key=lambda f: f[2] * f[3])
            face2_info = max(faces2, key=lambda f: f[2] * f[3])
            embedding1 = extract_face_embedding_enhanced(processed_img1, face1_info)
            embedding2 = extract_face_embedding_enhanced(processed_img2, face2_info)
            if embedding1 is None:
                return {"success": False, "message": "Không thể trích xuất embedding từ ảnh 1", "similarity": -1.0}
            if embedding2 is None:
                return {"success": False, "message": "Không thể trích xuất embedding từ ảnh 2", "similarity": -1.0}
            similarity = compare_embeddings_enhanced(embedding1, embedding2)
            from app.core.face_embeddings import make_face_decision
            is_same, confidence, message = make_face_decision(similarity, COSINE_THRESHOLD)
            return {"success": True, "is_same_person": is_same, "similarity": similarity, "confidence": confidence, "message": message, "threshold": COSINE_THRESHOLD}
        except Exception as e:
            print(f"Lỗi trong quy trình so sánh: {str(e)}")
            return {"success": False, "message": f"Lỗi: {str(e)}", "similarity": -1.0}


