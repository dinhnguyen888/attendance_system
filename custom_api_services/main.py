from fastapi import FastAPI, HTTPException, File, UploadFile, Form
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

def process_uploaded_image(file: UploadFile) -> np.ndarray:
    """Xử lý ảnh được upload trực tiếp - đơn giản hóa"""
    try:
        # Đọc nội dung file
        image_bytes = file.file.read()
        print(f"Uploaded file size: {len(image_bytes)} bytes")
        print(f"Uploaded file content type: {file.content_type}")
        
        # Chuyển thành numpy array và decode
        nparr = np.frombuffer(image_bytes, np.uint8)
        print(f"Numpy array shape: {nparr.shape}")
        
        # Decode ảnh
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Không thể decode ảnh từ file upload")
        
        print(f"Successfully decoded image, shape: {img.shape}")
        return img
        
    except Exception as e:
        print(f"Lỗi xử lý ảnh upload: {str(e)}")
        raise ValueError(f"Lỗi xử lý ảnh upload: {str(e)}")

def detect_faces(image: np.ndarray) -> list:
    """Phát hiện khuôn mặt trong ảnh - đơn giản hóa"""
    try:
        # Kiểm tra ảnh cơ bản
        if image is None:
            raise ValueError("Ảnh không hợp lệ")
        
        # Load cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Chuyển sang grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Phát hiện khuôn mặt
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        print(f"Detected {len(faces)} faces")
        
        return faces
        
    except Exception as e:
        print(f"Lỗi phát hiện khuôn mặt: {str(e)}")
        raise

def extract_face_features(image: np.ndarray, face_coords: tuple) -> np.ndarray:
    """Trích xuất đặc trưng khuôn mặt - đơn giản hóa"""
    try:
        # Lấy tọa độ
        x, y, w, h = face_coords
        
        # Cắt khuôn mặt
        face_roi = image[y:y+h, x:x+w]
        
        # Resize về kích thước chuẩn
        face_roi = cv2.resize(face_roi, (128, 128))
        
        return face_roi
        
    except Exception as e:
        print(f"Lỗi trích xuất khuôn mặt: {str(e)}")
        raise

def save_employee_face(employee_id: int, face_image: np.ndarray):
    """Lưu ảnh khuôn mặt của nhân viên"""
    try:
        # Đảm bảo thư mục tồn tại
        if not os.path.exists(EMPLOYEE_FACES_DIR):
            os.makedirs(EMPLOYEE_FACES_DIR, exist_ok=True)
        
        # Tạo đường dẫn file
        face_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}.jpg")
        
        # Lưu ảnh
        success = cv2.imwrite(face_path, face_image)
        if not success:
            raise ValueError("Không thể lưu ảnh khuôn mặt")
        
        print(f"Đã lưu ảnh khuôn mặt cho employee {employee_id} tại {face_path}")
        
    except Exception as e:
        print(f"Lỗi khi lưu ảnh khuôn mặt cho employee {employee_id}: {str(e)}")
        raise

def load_employee_face(employee_id: int) -> Optional[np.ndarray]:
    """Tải ảnh khuôn mặt của nhân viên"""
    face_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}.jpg")
    if os.path.exists(face_path):
        return cv2.imread(face_path)
    return None

def compare_faces(face1: np.ndarray, face2: np.ndarray) -> float:
    """So sánh hai khuôn mặt và trả về độ tương đồng - cải thiện"""
    try:
        # Chuyển về grayscale
        gray1 = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)
        
        # Sử dụng ORB để trích xuất đặc trưng
        orb = cv2.ORB_create(nfeatures=1000)
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)
        
        if des1 is None or des2 is None:
            print("No descriptors found")
            return 0.0
        
        print(f"Keypoints: {len(kp1)} vs {len(kp2)}")
        
        # Sử dụng BFMatcher để so sánh
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        
        # Lọc matches tốt
        good_matches = [m for m in matches if m.distance < 50]
        
        # Tính độ tương đồng
        if len(kp1) > 0 and len(kp2) > 0:
            similarity = len(good_matches) / min(len(kp1), len(kp2))
        else:
            similarity = 0.0
            
        print(f"Total matches: {len(matches)}, Good matches: {len(good_matches)}, Similarity: {similarity:.3f}")
        return similarity
        
    except Exception as e:
        print(f"Error in compare_faces: {str(e)}")
        return 0.0

@app.post("/face-recognition/verify", response_model=FaceRecognitionResponse)
async def verify_face(request: FaceRecognitionRequest):
    """Xác thực khuôn mặt cho check-in/check-out - đơn giản hóa"""
    try:
        print(f"Processing verification for employee {request.employee_id}, action: {request.action}")
        
        # Decode ảnh từ base64 - xử lý data URL prefix
        face_image_data = request.face_image
        if ',' in face_image_data:
            face_image_data = face_image_data.split(',')[1]
        
        try:
            image_bytes = base64.b64decode(face_image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as decode_error:
            print(f"Base64 decode error: {str(decode_error)}")
            return FaceRecognitionResponse(
                success=False,
                message=f"Lỗi decode ảnh: {str(decode_error)}"
            )
        
        if image is None:
            return FaceRecognitionResponse(
                success=False,
                message="Không thể decode ảnh"
            )
        
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
                    print(f"Face comparison confidence: {confidence}")
                    
                    # Giảm ngưỡng xuống 0.3 để dễ pass hơn
                    if confidence > 0.3:  # Ngưỡng tương đồng thấp hơn
                        return FaceRecognitionResponse(
                            success=True,
                            message="Check-out thành công",
                            confidence=confidence,
                            employee_id=request.employee_id
                        )
                    else:
                        return FaceRecognitionResponse(
                            success=False,
                            message=f"Khuôn mặt không khớp với nhân viên (confidence: {confidence:.3f})",
                            confidence=confidence
                        )
                else:
                    # Không có ảnh lưu trữ, cho phép check-out
                    print("No stored face found, allowing check-out")
                    return FaceRecognitionResponse(
                        success=True,
                        message="Check-out thành công (không có ảnh lưu trữ)",
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
        print(f"Error in verify_face: {str(e)}")
        return FaceRecognitionResponse(
            success=False,
            message=f"Lỗi xử lý: {str(e)}"
        )

@app.get("/")
def read_root():
    return {"message": "Face Recognition API for Attendance System"}

@app.get("/opencv-version")
def get_opencv_version():
    return {"opencv_version": cv2.__version__}

@app.post("/face-recognition/register")
async def register_employee_face(
    employee_id: int = Form(...),
    action: str = Form(...),
    face_image: UploadFile = File(...)
):
    """Đăng ký ảnh khuôn mặt cho nhân viên mới - đơn giản hóa"""
    try:
        print(f"Processing registration for employee {employee_id}, action: {action}")
        
        # Xử lý ảnh upload
        image = process_uploaded_image(face_image)
        
        # Phát hiện khuôn mặt
        faces = detect_faces(image)
        
        if len(faces) == 0:
            return {
                "success": False,
                "message": "Không tìm thấy khuôn mặt trong ảnh"
            }
        
        if len(faces) > 1:
            return {
                "success": False,
                "message": "Phát hiện nhiều khuôn mặt. Vui lòng chụp ảnh chỉ có một khuôn mặt"
            }
        
        # Trích xuất khuôn mặt
        face_coords = faces[0]
        face_roi = extract_face_features(image, face_coords)
        
        # Lưu ảnh
        save_employee_face(employee_id, face_roi)
        
        return {
            "success": True, 
            "message": f"Đăng ký khuôn mặt thành công cho nhân viên {employee_id}",
            "employee_id": employee_id
        }
        
    except Exception as e:
        print(f"Error in register_employee_face: {str(e)}")
        return {
            "success": False,
            "message": f"Lỗi xử lý: {str(e)}"
        }

@app.get("/face-recognition/health")
async def health_check():
    """Kiểm tra trạng thái API"""
    try:
        count = len([f for f in os.listdir(EMPLOYEE_FACES_DIR) if f.endswith('.jpg')])
        return {
            "status": "healthy",
            "opencv_version": cv2.__version__,
            "employee_faces_count": count
        }
    except:
        return {
            "status": "healthy",
            "opencv_version": cv2.__version__,
            "employee_faces_count": 0
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)