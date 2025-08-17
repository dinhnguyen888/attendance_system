from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cv2
import numpy as np
import base64
import json
from typing import Optional
import os

app = FastAPI(title="Face Recognition API", version="1.0.0")

# CORS middleware để cho phép Odoo gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FaceRecognitionRequest(BaseModel):
    face_image: str
    employee_id: Optional[int] = None
    action: str  # "check_in" hoặc "check_out"

class FaceRecognitionResponse(BaseModel):
    success: bool
    message: str
    confidence: Optional[float] = None
    employee_id: Optional[int] = None

# Thư mục lưu trữ ảnh khuôn mặt của nhân viên
EMPLOYEE_FACES_DIR = "employee_faces"
if not os.path.exists(EMPLOYEE_FACES_DIR):
    os.makedirs(EMPLOYEE_FACES_DIR)

def decode_base64_image(image_data: str) -> np.ndarray:
    """Decode base64 image string thành numpy array"""
    try:
        # Loại bỏ data URL prefix nếu có
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

def detect_faces(image: np.ndarray) -> list:
    """Phát hiện khuôn mặt trong ảnh"""
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return faces

def extract_face_features(image: np.ndarray, face_coords: tuple) -> np.ndarray:
    """Trích xuất đặc trưng khuôn mặt"""
    x, y, w, h = face_coords
    face_roi = image[y:y+h, x:x+w]
    # Resize về kích thước chuẩn
    face_roi = cv2.resize(face_roi, (128, 128))
    return face_roi

def compare_faces(face1: np.ndarray, face2: np.ndarray) -> float:
    """So sánh hai khuôn mặt và trả về độ tương đồng"""
    # Chuyển về grayscale
    gray1 = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)
    
    # Sử dụng ORB để trích xuất đặc trưng
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)
    
    if des1 is None or des2 is None:
        return 0.0
    
    # Sử dụng BFMatcher để so sánh
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    
    # Tính độ tương đồng
    similarity = len(matches) / max(len(kp1), len(kp2))
    return similarity

def save_employee_face(employee_id: int, face_image: np.ndarray):
    """Lưu ảnh khuôn mặt của nhân viên"""
    face_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}.jpg")
    cv2.imwrite(face_path, face_image)

def load_employee_face(employee_id: int) -> Optional[np.ndarray]:
    """Tải ảnh khuôn mặt của nhân viên"""
    face_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}.jpg")
    if os.path.exists(face_path):
        return cv2.imread(face_path)
    return None

@app.get("/")
def read_root():
    return {"message": "Face Recognition API for Attendance System"}

@app.get("/opencv-version")
def get_opencv_version():
    return {"opencv_version": cv2.__version__}

@app.post("/face-recognition/verify", response_model=FaceRecognitionResponse)
async def verify_face(request: FaceRecognitionRequest):
    """Xác thực khuôn mặt cho check-in/check-out"""
    try:
        # Decode ảnh từ base64
        image = decode_base64_image(request.face_image)
        
        # Phát hiện khuôn mặt
        faces = detect_faces(image)
        
        if len(faces) == 0:
            return FaceRecognitionResponse(
                success=False,
                message="Không tìm thấy khuôn mặt trong ảnh"
            )
        
        if len(faces) > 1:
            return FaceRecognitionResponse(
                success=False,
                message="Phát hiện nhiều khuôn mặt. Vui lòng chụp ảnh chỉ có một khuôn mặt"
            )
        
        # Trích xuất khuôn mặt
        face_coords = faces[0]
        current_face = extract_face_features(image, face_coords)
        
        if request.action == "check_in":
            # Lưu ảnh khuôn mặt cho nhân viên (nếu có employee_id)
            if request.employee_id:
                save_employee_face(request.employee_id, current_face)
                return FaceRecognitionResponse(
                    success=True,
                    message="Check-in thành công",
                    confidence=1.0,
                    employee_id=request.employee_id
                )
            else:
                return FaceRecognitionResponse(
                    success=True,
                    message="Check-in thành công",
                    confidence=1.0
                )
        
        elif request.action == "check_out":
            # So sánh với ảnh đã lưu (nếu có employee_id)
            if request.employee_id:
                stored_face = load_employee_face(request.employee_id)
                if stored_face is not None:
                    confidence = compare_faces(current_face, stored_face)
                    if confidence > 0.6:  # Ngưỡng tương đồng
                        return FaceRecognitionResponse(
                            success=True,
                            message="Check-out thành công",
                            confidence=confidence,
                            employee_id=request.employee_id
                        )
                    else:
                        return FaceRecognitionResponse(
                            success=False,
                            message="Khuôn mặt không khớp với nhân viên",
                            confidence=confidence
                        )
                else:
                    # Không có ảnh lưu trữ, cho phép check-out
                    return FaceRecognitionResponse(
                        success=True,
                        message="Check-out thành công",
                        confidence=1.0,
                        employee_id=request.employee_id
                    )
            else:
                return FaceRecognitionResponse(
                    success=True,
                    message="Check-out thành công",
                    confidence=1.0
                )
        
        else:
            return FaceRecognitionResponse(
                success=False,
                message="Hành động không hợp lệ"
            )
            
    except Exception as e:
        return FaceRecognitionResponse(
            success=False,
            message=f"Lỗi xử lý: {str(e)}"
        )

@app.post("/face-recognition/register")
async def register_employee_face(employee_id: int, request: FaceRecognitionRequest):
    """Đăng ký ảnh khuôn mặt cho nhân viên mới"""
    try:
        image = decode_base64_image(request.face_image)
        faces = detect_faces(image)
        
        if len(faces) == 0:
            raise HTTPException(status_code=400, detail="Không tìm thấy khuôn mặt")
        
        if len(faces) > 1:
            raise HTTPException(status_code=400, detail="Phát hiện nhiều khuôn mặt")
        
        face_coords = faces[0]
        face_roi = extract_face_features(image, face_coords)
        save_employee_face(employee_id, face_roi)
        
        return {"success": True, "message": f"Đăng ký khuôn mặt thành công cho nhân viên {employee_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/face-recognition/health")
async def health_check():
    """Kiểm tra trạng thái API"""
    return {
        "status": "healthy",
        "opencv_version": cv2.__version__,
        "employee_faces_count": len([f for f in os.listdir(EMPLOYEE_FACES_DIR) if f.endswith('.jpg')])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)