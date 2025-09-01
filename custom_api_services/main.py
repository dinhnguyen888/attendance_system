from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cv2
import numpy as np
import base64
import json
from typing import Optional, Tuple
import os
import tempfile
import threading
import math
os.environ["INSIGHTFACE_USE_TORCH"] = "0"
os.environ["ONNXRUNTIME_FORCE_CPU"] = "1"
# InsightFace (ArcFace embeddings) for high-accuracy face comparison
try:
    from insightface.app import FaceAnalysis
    _INSIGHTFACE_AVAILABLE = True
except Exception as _e:  # pragma: no cover
    print(f"InsightFace not available: {_e}")
    _INSIGHTFACE_AVAILABLE = False



app = FastAPI(title="Face Recognition API", version="1.0.0")

# CORS middleware để cho phép Odoo gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thư mục lưu trữ ảnh khuôn mặt của nhân viên
EMPLOYEE_FACES_DIR = "employee_faces"
if not os.path.exists(EMPLOYEE_FACES_DIR):
    os.makedirs(EMPLOYEE_FACES_DIR)

# Path helper for stored embeddings
def _employee_embedding_path(employee_id: int) -> str:
    return os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}.npy")

# Verification threshold and storage policy
COSINE_THRESHOLD = 0.7  # Threshold khắt khe hơn để tránh false accept
MAX_EMBEDDINGS_PER_EMPLOYEE = 5

# Lazy global model for embeddings
_face_app = None
_model_lock = threading.Lock()

def _get_face_app() -> Optional["FaceAnalysis"]:
    if not _INSIGHTFACE_AVAILABLE:
        return None
    global _face_app
    if _face_app is None:
        with _model_lock:
            if _face_app is None:
                app = FaceAnalysis(name="buffalo_l")
                # CPU mode: ctx_id=-1
                app.prepare(ctx_id=-1, det_size=(640, 640))
                _face_app = app
    return _face_app

def get_face_embedding(image: np.ndarray, face_coords: Optional[tuple] = None) -> Optional[np.ndarray]:
    """Compute a 512-dim normalized embedding using InsightFace. Returns None if unavailable/failure.

    If face_coords provided, crop to ROI first to help the detector; otherwise run on full image.
    """
    app = _get_face_app()
    if app is None:
        return None
    try:
        roi_img = image
        if face_coords is not None:
            x, y, w, h = face_coords
            roi_img = image[y:y+h, x:x+w]
        faces = app.get(roi_img)
        if not faces:
            # As a fallback, try full image if we initially cropped
            if roi_img is not image:
                faces = app.get(image)
                if not faces:
                    return None
            else:
                return None
        # Choose face with largest bbox
        face_obj = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        emb = face_obj.normed_embedding
        if emb is None:
            return None
        emb = np.asarray(emb, dtype=np.float32)
        # Ensure L2 normalization
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb
    except Exception as e:
        print(f"Error computing embedding: {str(e)}")
        return None

def save_employee_embedding(employee_id: int, embedding: np.ndarray) -> None:
    try:
        path = _employee_embedding_path(employee_id)
        stacked: Optional[np.ndarray] = None
        if os.path.exists(path):
            try:
                existing = np.load(path)
                if existing.ndim == 1 and existing.shape[0] == embedding.shape[0]:
                    stacked = np.stack([existing, embedding], axis=0)
                elif existing.ndim == 2 and existing.shape[1] == embedding.shape[0]:
                    stacked = np.vstack([existing, embedding[None, :]])
                else:
                    stacked = embedding[None, :]
            except Exception as _e:
                print(f"Không đọc được embeddings cũ cho employee {employee_id}: {_e}")
                stacked = embedding[None, :]
        else:
            stacked = embedding[None, :]

        # Giữ tối đa N embedding gần nhất
        if stacked.shape[0] > MAX_EMBEDDINGS_PER_EMPLOYEE:
            stacked = stacked[-MAX_EMBEDDINGS_PER_EMPLOYEE:, :]

        np.save(path, stacked)
    except Exception as e:
        print(f"Lỗi khi lưu embedding cho employee {employee_id}: {str(e)}")

def load_employee_embeddings(employee_id: int) -> Optional[np.ndarray]:
    try:
        path = _employee_embedding_path(employee_id)
        if not os.path.exists(path):
            return None
        emb = np.load(path)
        # Ensure 2D array (num_samples, 512)
        if emb.ndim == 1:
            emb = emb[None, :]
        # Normalize rows
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        emb = (emb / norms).astype(np.float32)
        return emb
    except Exception as e:
        print(f"Lỗi khi tải embeddings cho employee {employee_id}: {str(e)}")
        return None

def process_uploaded_image(file: UploadFile) -> np.ndarray:
    """Xử lý ảnh được upload trực tiếp"""
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
    """Phát hiện khuôn mặt trong ảnh"""
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
    """Trích xuất đặc trưng khuôn mặt"""
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

def validate_image_aspect_ratio(image: np.ndarray) -> Tuple[bool, str]:
    """Kiểm tra tỉ lệ khung hình của ảnh (3:4 hoặc 4:6)"""
    try:
        height, width = image.shape[:2]
        
        # Tính tỉ lệ khung hình
        aspect_ratio = width / height
        
        # Kiểm tra tỉ lệ 3:4 (0.75) với độ dung sai 5%
        ratio_3_4 = 3.0 / 4.0
        tolerance = 0.05
        
        if abs(aspect_ratio - ratio_3_4) <= tolerance:
            return True, "3:4"
        
        # Kiểm tra tỉ lệ 4:6 (2:3 = 0.667) với độ dung sai 5%
        ratio_4_6 = 4.0 / 6.0  # = 2/3
        
        if abs(aspect_ratio - ratio_4_6) <= tolerance:
            return True, "4:6"
        
        return False, f"Tỉ lệ hiện tại: {aspect_ratio:.3f}. Yêu cầu tỉ lệ 3:4 (0.75) hoặc 4:6 (0.667)"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra tỉ lệ khung hình: {str(e)}"

def validate_background_color(image: np.ndarray) -> Tuple[bool, str]:
    """Kiểm tra màu nền của ảnh (trắng hoặc xanh)"""
    try:
        # Lấy các pixel ở viền ảnh để xác định màu nền
        height, width = image.shape[:2]
        
        # Lấy pixel từ 4 cạnh của ảnh
        border_pixels = []
        
        # Cạnh trên và dưới
        border_pixels.extend(image[0, :].reshape(-1, 3))
        border_pixels.extend(image[height-1, :].reshape(-1, 3))
        
        # Cạnh trái và phải
        border_pixels.extend(image[:, 0].reshape(-1, 3))
        border_pixels.extend(image[:, width-1].reshape(-1, 3))
        
        border_pixels = np.array(border_pixels)
        
        # Tính màu trung bình của viền
        avg_color = np.mean(border_pixels, axis=0)
        
        # Chuyển từ BGR sang RGB để dễ hiểu
        avg_color_rgb = avg_color[::-1]  # BGR to RGB
        
        # Định nghĩa màu trắng và xanh dương trong RGB
        white_rgb = np.array([255, 255, 255])
        blue_rgb = np.array([0, 0, 255])  # Xanh dương thuần
        light_blue_rgb = np.array([173, 216, 230])  # Xanh nhạt
        
        # Tính khoảng cách Euclidean
        dist_to_white = np.linalg.norm(avg_color_rgb - white_rgb)
        dist_to_blue = np.linalg.norm(avg_color_rgb - blue_rgb)
        dist_to_light_blue = np.linalg.norm(avg_color_rgb - light_blue_rgb)
        
        # Ngưỡng chấp nhận (có thể điều chỉnh)
        white_threshold = 50  # Cho phép sai lệch 50 đơn vị
        blue_threshold = 150   # Cho phép sai lệch 80 đơn vị cho màu xanh
        
        if dist_to_white <= white_threshold:
            return True, "Nền trắng"
        elif dist_to_blue <= blue_threshold or dist_to_light_blue <= blue_threshold:
            return True, "Nền xanh"
        else:
            return False, f"Màu nền không hợp lệ. Màu trung bình: RGB({avg_color_rgb[0]:.0f}, {avg_color_rgb[1]:.0f}, {avg_color_rgb[2]:.0f}). Yêu cầu nền trắng hoặc xanh."
            
    except Exception as e:
        return False, f"Lỗi kiểm tra màu nền: {str(e)}"

def scale_image_to_standard(image: np.ndarray, target_width: int = 480) -> np.ndarray:
    """Scale ảnh về kích thước chuẩn để tối ưu cho việc phát hiện khuôn mặt"""
    try:
        height, width = image.shape[:2]
        
        # Tính tỉ lệ scale dựa trên chiều rộng mục tiêu
        scale_ratio = target_width / width
        
        # Tính chiều cao mới để giữ nguyên tỉ lệ khung hình
        target_height = int(height * scale_ratio)
        
        # Resize ảnh
        scaled_image = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
        
        print(f"Scaled image from {width}x{height} to {target_width}x{target_height}")
        return scaled_image
        
    except Exception as e:
        print(f"Lỗi khi scale ảnh: {str(e)}")
        return image  # Trả về ảnh gốc nếu có lỗi

def compare_faces(face1: np.ndarray, face2: np.ndarray) -> float:
    """So sánh hai khuôn mặt và trả về độ tương đồng (cosine similarity)."""
    try:
        # Try embeddings if possible
        emb1 = get_face_embedding(face1)
        emb2 = get_face_embedding(face2)
        if emb1 is not None and emb2 is not None:
            similarity = float(np.dot(emb1, emb2))  # cosine similarity in [-1, 1]
            print(f"Embedding cosine similarity: {similarity:.3f}")
            return similarity

        # Fallback: ORB + FLANN
        gray1 = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)

        orb = cv2.ORB_create(nfeatures=5000)
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)

        if des1 is None or des2 is None or len(kp1) == 0 or len(kp2) == 0:
            print("Không tìm thấy đặc trưng để so sánh")
            return -1.0

        index_params = dict(algorithm=6, table_number=6, key_size=12, multi_probe_level=1)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1, des2, k=2)

        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

        # Map ORB similarity to cosine scale [-1, 1]
        orb_similarity = len(good_matches) / min(len(kp1), len(kp2))
        similarity = 2.0 * orb_similarity - 1.0
        print(f"ORB matches: {len(matches)}, Good: {len(good_matches)}, Mapped similarity: {similarity:.3f}")
        return similarity

    except Exception as e:
        print(f"Error in compare_faces: {str(e)}")
        return -1.0

@app.post("/face-recognition/verify")
async def verify_face(
    face_image: UploadFile = File(...),
    action: str = Form(...),
    employee_id: int = Form(...)
):
    """Xác thực khuôn mặt cho check-in/check-out"""
    try:
        print(f"Processing verification for employee {employee_id}, action: {action}")
        
        # Xử lý ảnh upload
        image = process_uploaded_image(face_image)
        
        # Phát hiện khuôn mặt
        faces = detect_faces(image)
        
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
        
        # Trích xuất khuôn mặt
        face_coords = faces[0]
        current_embedding = get_face_embedding(image, face_coords)
        
        if current_embedding is None:
            return {
                "success": False,
                "message": "Không thể trích xuất embedding từ ảnh",
                "confidence": 0.0,
                "employee_id": employee_id
            }
        
        # Kiểm tra xem nhân viên đã đăng ký chưa
        stored_embeddings = load_employee_embeddings(employee_id)
        
        if stored_embeddings is None:
            # Nếu chưa có embedding, thử lấy ảnh khuôn mặt đã đăng ký và tạo embedding từ đó
            registered_face = load_employee_face(employee_id)
            if registered_face is not None:
                # Thử trích xuất embedding trực tiếp
                registered_embedding = get_face_embedding(registered_face)
                # Nếu thất bại, thử lại với bbox phủ toàn ảnh đã cắt
                if registered_embedding is None:
                    try:
                        h, w = registered_face.shape[:2]
                        registered_embedding = get_face_embedding(registered_face, (0, 0, w, h))
                    except Exception:
                        registered_embedding = None
                if registered_embedding is not None:
                    # Lưu embedding lần đầu
                    save_employee_embedding(employee_id, registered_embedding)
                    stored_embeddings = load_employee_embeddings(employee_id)
            # Nếu vẫn không tạo được từ ảnh đăng ký, khởi tạo bằng embedding hiện tại
            if stored_embeddings is None and current_embedding is not None:
                save_employee_embedding(employee_id, current_embedding)
                stored_embeddings = load_employee_embeddings(employee_id)
            if stored_embeddings is None:
                return {
                    "success": False,
                    "message": "Nhân viên chưa đăng ký khuôn mặt. Vui lòng đăng ký trước",
                    "confidence": 0.0,
                    "employee_id": employee_id
                }
        
        # Tính cosine similarity với tất cả embeddings đã lưu
        sims = stored_embeddings @ current_embedding
        max_sim = float(np.max(sims))
        avg_sim = float(np.mean(sims))
        
        print(f"Face verification — avg: {avg_sim:.3f}, max: {max_sim:.3f}, samples: {stored_embeddings.shape[0]}")
        
        if max_sim >= COSINE_THRESHOLD:
            return {
                "success": True,
                "message": f"{action.capitalize()} thành công",
                "confidence": max_sim,
                "employee_id": employee_id
            }
        else:
            return {
                "success": False,
                "message": f"Khuôn mặt không khớp với nhân viên (max cosine: {max_sim:.3f})",
                "confidence": max_sim,
                "employee_id": employee_id
            }
            
    except Exception as e:
        print(f"Error in verify_face: {str(e)}")
        return {
            "success": False,
            "message": f"Lỗi xử lý: {str(e)}",
            "confidence": 0.0,
            "employee_id": employee_id
        }

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
    print(f"Processing registration for employee {employee_id}, action: {action}")
    
    """Đăng ký ảnh khuôn mặt cho nhân viên mới"""
    try:
        print(f"Processing registration for employee {employee_id}, action: {action}")
        
        # Xử lý ảnh upload
        image = process_uploaded_image(face_image)
        
        # Kiểm tra tỉ lệ khung hình
        aspect_valid, aspect_msg = validate_image_aspect_ratio(image)
        if not aspect_valid:
            return {
                "success": False,
                "message": f"Tỉ lệ khung hình không hợp lệ: {aspect_msg}"
            }
        
        # Kiểm tra màu nền
        bg_valid, bg_msg = validate_background_color(image)
        if not bg_valid:
            return {
                "success": False,
                "message": f"Màu nền không hợp lệ: {bg_msg}"
            }
        
        print(f"Image validation passed: {aspect_msg}, {bg_msg}")
        
        # Scale ảnh về kích thước chuẩn để tối ưu phát hiện khuôn mặt
        image = scale_image_to_standard(image)
        
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
                "message": "Phát hiện nhiều khuôn mặt. Vui lòng chụp ảnh chỉ có một khuôn mặt",
                "confidence": 0.0
            }
        
        # Trích xuất khuôn mặt
        face_coords = faces[0]
        face_roi = extract_face_features(image, face_coords)
        
        # Lưu ảnh khuôn mặt, KHÔNG lưu embedding ở bước đăng ký
        save_employee_face(employee_id, face_roi)
        
        # Thử tạo và lưu embedding luôn để lần xác thực đầu tiên không bị thiếu
        try:
            initial_embedding = get_face_embedding(image, face_coords)
            if initial_embedding is None:
                # Thử lại với toàn bộ ảnh đã cắt (ROI 128x128)
                h, w = face_roi.shape[:2]
                initial_embedding = get_face_embedding(face_roi, (0, 0, w, h))
            if initial_embedding is not None:
                save_employee_embedding(employee_id, initial_embedding)
        except Exception as _e:
            print(f"Không thể tạo embedding khi đăng ký cho employee {employee_id}: {_e}")
        
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

@app.delete("/face-recognition/employee/{employee_id}")
async def delete_employee_face(employee_id: int):
    """Xóa ảnh khuôn mặt và embedding của nhân viên"""
    try:
        deleted_files = []
        errors = []
        
        # Xóa ảnh khuôn mặt
        face_path = os.path.join(EMPLOYEE_FACES_DIR, f"employee_{employee_id}.jpg")
        if os.path.exists(face_path):
            try:
                os.remove(face_path)
                deleted_files.append(f"employee_{employee_id}.jpg")
                print(f"Deleted face image: {face_path}")
            except Exception as e:
                errors.append(f"Cannot delete face image: {str(e)}")
        
        # Xóa embedding
        embedding_path = _employee_embedding_path(employee_id)
        if os.path.exists(embedding_path):
            try:
                os.remove(embedding_path)
                deleted_files.append(f"employee_{employee_id}.npy")
                print(f"Deleted embedding: {embedding_path}")
            except Exception as e:
                errors.append(f"Cannot delete embedding: {str(e)}")
        
        if not deleted_files and not errors:
            return {
                "success": False,
                "message": f"Không tìm thấy dữ liệu cho nhân viên {employee_id}",
                "employee_id": employee_id,
                "deleted_files": [],
                "errors": []
            }
        
        success = len(errors) == 0
        message = f"Đã xóa thành công dữ liệu cho nhân viên {employee_id}" if success else f"Xóa một phần dữ liệu cho nhân viên {employee_id}"
        
        return {
            "success": success,
            "message": message,
            "employee_id": employee_id,
            "deleted_files": deleted_files,
            "errors": errors
        }
        
    except Exception as e:
        print(f"Error in delete_employee_face: {str(e)}")
        return {
            "success": False,
            "message": f"Lỗi khi xóa dữ liệu nhân viên: {str(e)}",
            "employee_id": employee_id,
            "deleted_files": [],
            "errors": [str(e)]
        }

@app.get("/face-recognition/health")
async def health_check():
    """Kiểm tra trạng thái API"""
    try:
        count = len([f for f in os.listdir(EMPLOYEE_FACES_DIR) if f.endswith('.jpg')])
        status = {
            "status": "healthy",
            "opencv_version": cv2.__version__,
            "employee_faces_count": count,
            "insightface": _INSIGHTFACE_AVAILABLE,
            "cosine_threshold": COSINE_THRESHOLD
        }
        try:
            if _INSIGHTFACE_AVAILABLE and _get_face_app() is not None:
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

@app.post("/face-recognition/backfill-embeddings")
async def backfill_embeddings():
    """Tạo embeddings từ các ảnh đã đăng ký sẵn trong thư mục employee_faces."""
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
                # Bỏ qua nếu đã có embedding
                emb_path = _employee_embedding_path(employee_id)
                if os.path.exists(emb_path):
                    processed += 1
                    continue
                img = cv2.imread(os.path.join(EMPLOYEE_FACES_DIR, f))
                if img is None:
                    failed.append({"file": f, "reason": "cannot read"})
                    continue
                faces = detect_faces(img)
                emb = None
                if len(faces) > 0:
                    emb = get_face_embedding(img, faces[0])
                if emb is None:
                    # Thử toàn bộ ảnh
                    h, w = img.shape[:2]
                    emb = get_face_embedding(img, (0, 0, w, h))
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)