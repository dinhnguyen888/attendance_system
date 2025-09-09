"""
FastAPI routes for face recognition endpoints
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import Dict, Any
import cv2
import os
import numpy as np
from app.services.face_recognition_service import FaceRecognitionService
from app.models.face_models import is_insightface_available
from app.config import *
from app.core.face_embeddings import load_employee_embeddings, save_employee_embedding, get_face_embedding
from app.core.image_processing import preprocess_image
from app.core.face_detection import detect_faces_insightface

router = APIRouter()
face_service = FaceRecognitionService()

@router.post("/face-recognition/register")
async def register_employee_face(
    employee_id: int = Form(...),
    action: str = Form(...),
    face_image: UploadFile = File(...)
) -> Dict[str, Any]:
    """Register employee face with validation and feature extraction"""
    return face_service.register_employee_face(employee_id, face_image, action)

@router.post("/face-recognition/verify")
async def verify_face(
    face_image: UploadFile = File(...),
    action: str = Form(...),
    employee_id: int = Form(...)
) -> Dict[str, Any]:
    """Verify face for check-in/check-out"""
    return face_service.verify_employee_face(employee_id, face_image, action)

@router.post("/face-recognition/compare")
async def compare_two_faces(
    face_image1: UploadFile = File(...),
    face_image2: UploadFile = File(...)
) -> Dict[str, Any]:
    """API endpoint to test complete face comparison workflow"""
    return face_service.compare_two_faces(face_image1, face_image2)

@router.delete("/face-recognition/employee/{employee_id}")
async def delete_employee_face(employee_id: int) -> Dict[str, Any]:
    """Delete employee face image and embeddings"""
    return face_service.delete_employee_data(employee_id)

@router.get("/face-recognition/health")
async def health_check() -> Dict[str, Any]:
    """Check API status"""
    try:
        count = len([f for f in os.listdir(EMPLOYEE_FACES_DIR) if f.endswith('.jpg')])
        status = {
            "status": "healthy",
            "opencv_version": cv2.__version__,
            "employee_faces_count": count,
            "insightface": is_insightface_available(),
            "cosine_threshold": COSINE_THRESHOLD
        }
        try:
            if is_insightface_available():
                from app.models.face_models import get_face_app
                if get_face_app() is not None:
                    status["embedding_model"] = "buffalo_l"
            # Count embedding files and total samples
            emb_files = [f for f in os.listdir(EMPLOYEE_FACES_DIR) if f.endswith('.npy')]
            total_samples = 0
            for f in emb_files:
                try:
                    arr = np.load(os.path.join(EMPLOYEE_FACES_DIR, f))
                    if arr.ndim == 1:
                        total_samples += 1
                    elif arr.ndim == 2:
                        total_samples += int(arr.shape[0])
                except Exception:
                    pass
            status["embedding_files"] = len(emb_files)
            status["embedding_samples"] = total_samples
        except Exception:
            pass
        return status
    except:
        return {
            "status": "healthy",
            "opencv_version": cv2.__version__,
            "employee_faces_count": 0
        }

@router.post("/face-recognition/backfill-embeddings")
async def backfill_embeddings() -> Dict[str, Any]:
    """Create embeddings from pre-registered images in employee_faces folder."""
    processed = 0
    created = 0
    failed = []
    try:
        files = [f for f in os.listdir(EMPLOYEE_FACES_DIR) if f.endswith('.jpg')]
        for f in files:
            try:
                if not f.startswith('employee_'):
                    continue
                employee_id_str = f[len('employee_'):-len('.jpg')]
                employee_id = int(employee_id_str)
                # Skip if embedding already exists
                from app.core.face_embeddings import _employee_embedding_path
                emb_path = _employee_embedding_path(employee_id)
                if os.path.exists(emb_path):
                    processed += 1
                    continue
                img = cv2.imread(os.path.join(EMPLOYEE_FACES_DIR, f))
                if img is None:
                    failed.append({"file": f, "reason": "cannot read"})
                    continue
                # Use standard workflow to create embedding
                from app.core.face_embeddings import extract_face_embedding_enhanced
                _, processed_img = preprocess_image(img)
                faces = detect_faces_insightface(processed_img)
                emb = None
                if len(faces) > 0:
                    emb = extract_face_embedding_enhanced(processed_img, faces[0])
                if emb is None:
                    # Fallback with old method
                    emb = get_face_embedding(img, (0, 0, img.shape[1], img.shape[0]))
                if emb is None:
                    failed.append({"file": f, "reason": "no embedding"})
                    continue
                save_employee_embedding(employee_id, emb)
                created += 1
                processed += 1
            except Exception as e:
                failed.append({"file": f, "reason": str(e)})
        return {
            "success": True,
            "processed": processed,
            "created": created,
            "failed": failed,
            "embedding_files": len([x for x in os.listdir(EMPLOYEE_FACES_DIR) if x.endswith('.npy')])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/face-recognition/info")
async def get_api_info() -> Dict[str, Any]:
    """Information about API and processing workflow"""
    return {
        "api_name": "Face Recognition API",
        "version": API_VERSION,
        "workflow": {
            "step_1": "Chuẩn bị và khởi tạo (InsightFace buffalo_l model)",
            "step_2": "Tiền xử lý ảnh (resize, normalize, color conversion)",
            "step_3": "Phát hiện khuôn mặt (InsightFace RetinaFace)",
            "step_4": "Căn chỉnh khuôn mặt (facial landmarks alignment)",
            "step_5": "Trích xuất đặc trưng (ArcFace embedding 512-dim)",
            "step_6": "So sánh độ tương đồng (cosine similarity)",
            "step_7": "Ra quyết định (threshold-based decision)"
        },
        "features": {
            "face_detection": "InsightFace RetinaFace + OpenCV Haar (fallback)",
            "face_alignment": "Facial landmarks-based affine transformation",
            "embedding_model": "ArcFace (buffalo_l)",
            "similarity_metric": "Cosine similarity",
            "threshold": COSINE_THRESHOLD,
            "image_validation": "3:4 aspect ratio + solid background"
        },
        "endpoints": {
            "/face-recognition/register": "Đăng ký khuôn mặt nhân viên",
            "/face-recognition/verify": "Xác thực khuôn mặt check-in/out",
            "/face-recognition/compare": "So sánh 2 khuôn mặt (test)",
            "/face-recognition/health": "Kiểm tra trạng thái API",
            "/face-recognition/info": "Thông tin API và workflow"
        }
    }

@router.get("/")
def read_root():
    return {"message": "Face Recognition API for Attendance System"}

@router.get("/opencv-version")
def get_opencv_version():
    return {"opencv_version": cv2.__version__}
