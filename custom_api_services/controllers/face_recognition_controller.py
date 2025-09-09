"""
Face recognition API controllers
"""
from fastapi import HTTPException, File, UploadFile, Form
from models.schemas import *
from services.image_processing_service import process_uploaded_image, preprocess_image, extract_face_region_only
from services.image_validation_service import validate_image_aspect_ratio, validate_background_color
from services.face_detection_service import detect_faces_insightface
from services.skin_normalization_service import normalize_skin_tone
from services.canny_features_service import (
    extract_canny_feature_points, 
    compare_canny_features,
    save_employee_canny_features,
    load_employee_canny_features
)
from services.file_storage_service import save_employee_face, delete_employee_files
from services.face_comparison_service import compare_faces_complete_workflow
from models.config import CANNY_THRESHOLD

async def verify_face(
    face_image: UploadFile = File(...),
    action: str = Form(...),
    employee_id: int = Form(...)
) -> FaceVerificationResponse:
    """Verify face for check-in/check-out"""
    try:
        print(f"Processing verification for employee {employee_id}, action: {action}")
        
        # Process uploaded image
        image = process_uploaded_image(face_image)
        
        # Step 2 & 3: Preprocess and detect faces according to standard workflow
        _, processed_image = preprocess_image(image)
        faces = detect_faces_insightface(processed_image)
        
        if len(faces) == 0:
            return FaceVerificationResponse(
                success=False,
                message="Không tìm thấy khuôn mặt trong ảnh",
                confidence=0.0,
                employee_id=employee_id
            )
        
        if len(faces) > 1:
            return FaceVerificationResponse(
                success=False,
                message="Phát hiện nhiều khuôn mặt. Vui lòng chụp ảnh chỉ có một khuôn mặt",
                confidence=0.0,
                employee_id=employee_id
            )
        
        # Step 4: Apply skin tone normalization before extracting features
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
            return FaceVerificationResponse(
                success=False,
                message="Nhân viên chưa đăng ký khuôn mặt. Vui lòng đăng ký trước",
                confidence=0.0,
                employee_id=employee_id
            )
        
        # Compare Canny feature points
        similarity = compare_canny_features(current_features, stored_features, threshold=0.1)
        
        print(f"Canny feature comparison — similarity: {similarity:.3f}")
        
        if similarity >= CANNY_THRESHOLD:
            return FaceVerificationResponse(
                success=True,
                message=f"{action.capitalize()} thành công",
                confidence=similarity,
                employee_id=employee_id
            )
        else:
            return FaceVerificationResponse(
                success=False,
                message=f"Khuôn mặt không khớp với nhân viên (similarity: {similarity:.3f})",
                confidence=similarity,
                employee_id=employee_id
            )
            
    except Exception as e:
        print(f"Error in verify_face: {str(e)}")
        return FaceVerificationResponse(
            success=False,
            message=f"Lỗi xử lý: {str(e)}",
            confidence=0.0,
            employee_id=employee_id
        )

async def register_employee_face(
    employee_id: int = Form(...),
    action: str = Form(...),
    face_image: UploadFile = File(...)
) -> FaceRegistrationResponse:
    """Register face image for new employee"""
    try:
        print(f"Processing registration for employee {employee_id}, action: {action}")
        
        # Process uploaded image
        image = process_uploaded_image(face_image)
        
        # Check aspect ratio
        aspect_valid, aspect_msg = validate_image_aspect_ratio(image)
        if not aspect_valid:
            return FaceRegistrationResponse(
                success=False,
                message=f"Tỉ lệ khung hình không hợp lệ: {aspect_msg}"
            )
        
        # Check background color
        bg_valid, bg_msg = validate_background_color(image)
        if not bg_valid:
            return FaceRegistrationResponse(
                success=False,
                message=f"Màu nền không hợp lệ: {bg_msg}"
            )
        
        print(f"Image validation passed: {aspect_msg}, {bg_msg}")
        
        # Detect faces directly on original image (no resize)
        faces = detect_faces_insightface(image)
        
        if len(faces) == 0:
            return FaceRegistrationResponse(
                success=False,
                message="Không tìm thấy khuôn mặt trong ảnh"
            )
        
        if len(faces) > 1:
            return FaceRegistrationResponse(
                success=False,
                message="Phát hiện nhiều khuôn mặt. Vui lòng chụp ảnh chỉ có một khuôn mặt",
                confidence=0.0
            )
        
        # Step 4: Apply skin tone normalization before extracting features
        face_info = faces[0]
        face_obj = face_info[4] if len(face_info) > 4 else None
        
        # Normalize skin tone on original image
        normalized_image = normalize_skin_tone(image, face_info[:4], face_obj)
        
        # Extract Canny feature points from normalized image
        canny_features = extract_canny_feature_points(normalized_image, face_obj, face_info[:4])
        
        if canny_features is None:
            return FaceRegistrationResponse(
                success=False,
                message="Không thể trích xuất đặc trưng khuôn mặt từ ảnh"
            )
        
        # Save Canny feature points
        save_employee_canny_features(employee_id, canny_features)
        
        # Crop and save only face region from original image (not resized image)
        face_region = extract_face_region_only(image, face_info[:4], margin_ratio=0.05)
        save_employee_face(employee_id, face_region)
        
        return FaceRegistrationResponse(
            success=True, 
            message=f"Đăng ký khuôn mặt thành công cho nhân viên {employee_id}",
            employee_id=employee_id,
            confidence=1.0
        )
        
    except Exception as e:
        print(f"Error in register_employee_face: {str(e)}")
        return FaceRegistrationResponse(
            success=False,
            message=f"Lỗi xử lý: {str(e)}",
            confidence=0.0,
            employee_id=None
        )

async def delete_employee_face(employee_id: int) -> DeleteEmployeeResponse:
    """Delete employee's face image and embedding"""
    try:
        deleted_files, errors = delete_employee_files(employee_id)
        
        if not deleted_files and not errors:
            return DeleteEmployeeResponse(
                success=False,
                message=f"Không tìm thấy dữ liệu cho nhân viên {employee_id}",
                employee_id=employee_id,
                deleted_files=[],
                errors=[]
            )
        
        success = len(errors) == 0
        message = f"Đã xóa thành công dữ liệu cho nhân viên {employee_id}" if success else f"Xóa một phần dữ liệu cho nhân viên {employee_id}"
        
        return DeleteEmployeeResponse(
            success=success,
            message=message,
            employee_id=employee_id,
            deleted_files=deleted_files,
            errors=errors
        )
        
    except Exception as e:
        print(f"Error in delete_employee_face: {str(e)}")
        return DeleteEmployeeResponse(
            success=False,
            message=f"Lỗi khi xóa dữ liệu nhân viên: {str(e)}",
            employee_id=employee_id,
            deleted_files=[],
            errors=[str(e)]
        )

async def compare_two_faces(
    face_image1: UploadFile = File(...),
    face_image2: UploadFile = File(...)
) -> FaceComparisonResponse:
    """API endpoint to test complete face comparison workflow"""
    try:
        print("=== TESTING COMPLETE FACE COMPARISON WORKFLOW ===")
        
        # Process 2 uploaded images
        image1 = process_uploaded_image(face_image1)
        image2 = process_uploaded_image(face_image2)
        
        # Run complete comparison workflow
        result = compare_faces_complete_workflow(image1, image2)
        
        return FaceComparisonResponse(
            success=result["success"],
            message=result["message"],
            similarity=result["similarity"],
            is_same_person=result.get("is_same_person"),
            confidence=result.get("confidence"),
            threshold=result.get("threshold")
        )
        
    except Exception as e:
        print(f"Error in compare_two_faces: {str(e)}")
        return FaceComparisonResponse(
            success=False,
            message=f"Lỗi xử lý: {str(e)}",
            similarity=-1.0
        )
