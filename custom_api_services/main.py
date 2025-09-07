from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cv2
import numpy as np
from typing import Optional, Tuple
import insightface
from insightface.app import FaceAnalysis
from scipy.spatial.distance import cosine, cdist
import math
import os
import threading

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

def preprocess_image(image: np.ndarray, target_size: tuple = (640, 640)) -> np.ndarray:
    """Bước 2: Tiền xử lý ảnh theo chuẩn InsightFace"""
    try:
        # Chuyển đổi color space từ BGR sang RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
        
        # Resize ảnh về kích thước phù hợp cho detection
        resized = cv2.resize(rgb_image, target_size, interpolation=cv2.INTER_LINEAR)
        
        # Chuẩn hóa pixel values về range [0,1]
        normalized = resized.astype(np.float32) / 255.0
        
        print(f"Preprocessed image: {image.shape} -> {resized.shape}, normalized to [0,1]")
        return normalized, resized
        
    except Exception as e:
        print(f"Lỗi tiền xử lý ảnh: {str(e)}")
        raise

def detect_faces_insightface(image: np.ndarray) -> list:
    """Bước 3: Phát hiện khuôn mặt bằng InsightFace RetinaFace"""
    try:
        app = _get_face_app()
        if app is None:
            # Fallback to OpenCV Haar cascades
            return detect_faces_opencv(image)
        
        # Sử dụng InsightFace để detect faces
        faces = app.get(image)
        
        if not faces:
            print("Không tìm thấy khuôn mặt bằng InsightFace")
            return []
        
        # Chuyển đổi format từ InsightFace sang OpenCV format (x, y, w, h)
        opencv_faces = []
        for face in faces:
            bbox = face.bbox.astype(int)
            x, y, x2, y2 = bbox
            w, h = x2 - x, y2 - y
            opencv_faces.append((x, y, w, h, face))  # Thêm face object để dùng landmarks
        
        print(f"InsightFace detected {len(opencv_faces)} faces")
        return opencv_faces
        
    except Exception as e:
        print(f"Lỗi phát hiện khuôn mặt InsightFace: {str(e)}")
        # Fallback to OpenCV
        return detect_faces_opencv(image)

def detect_faces_opencv(image: np.ndarray) -> list:
    """Fallback: Phát hiện khuôn mặt bằng OpenCV Haar cascades"""
    try:
        # Chuyển về BGR nếu cần cho OpenCV
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Kiểm tra xem có phải RGB không (giá trị trong [0,1])
            if image.max() <= 1.0:
                bgr_image = (image * 255).astype(np.uint8)
                bgr_image = cv2.cvtColor(bgr_image, cv2.COLOR_RGB2BGR)
            else:
                bgr_image = image
        else:
            bgr_image = image
        
        # Load cascade classifier với tham số tối ưu
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Chuyển sang grayscale
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        
        # Phát hiện khuôn mặt với tham số tối ưu
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.05,  # Tăng độ chính xác
            minNeighbors=6,    # Giảm false positive
            minSize=(80, 80),  # Kích thước tối thiểu
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Chuyển đổi format để tương thích
        opencv_faces = [(x, y, w, h, None) for x, y, w, h in faces]
        
        print(f"OpenCV detected {len(opencv_faces)} faces")
        return opencv_faces
        
    except Exception as e:
        print(f"Lỗi phát hiện khuôn mặt OpenCV: {str(e)}")
        return []

def align_face(image: np.ndarray, face_info: tuple) -> np.ndarray:
    """Bước 4: Căn chỉnh khuôn mặt sử dụng facial landmarks"""
    try:
        x, y, w, h, face_obj = face_info
        
        # Nếu có InsightFace face object với landmarks
        if face_obj is not None and hasattr(face_obj, 'kps') and face_obj.kps is not None:
            # Sử dụng landmarks từ InsightFace để align
            landmarks = face_obj.kps.astype(np.float32)
            
            # Định nghĩa landmarks chuẩn cho khuôn mặt 112x112
            standard_landmarks = np.array([
                [38.2946, 51.6963],  # Left eye
                [73.5318, 51.5014],  # Right eye  
                [56.0252, 71.7366],  # Nose tip
                [41.5493, 92.3655],  # Left mouth corner
                [70.7299, 92.2041]   # Right mouth corner
            ], dtype=np.float32)
            
            # Tính affine transformation matrix
            tform = cv2.estimateAffinePartial2D(landmarks, standard_landmarks)[0]
            
            # Áp dụng transformation
            aligned_face = cv2.warpAffine(image, tform, (112, 112))
            
            print("Face aligned using InsightFace landmarks")
            return aligned_face
        
        else:
            # Fallback: Crop và resize đơn giản
            return align_face_simple(image, (x, y, w, h))
            
    except Exception as e:
        print(f"Lỗi căn chỉnh khuôn mặt: {str(e)}")
        # Fallback to simple alignment
        x, y, w, h = face_info[:4]
        return align_face_simple(image, (x, y, w, h))

def normalize_skin_tone(image: np.ndarray, face_coords: tuple, face_obj=None) -> np.ndarray:
    """Chuẩn hóa màu da khuôn mặt về một màu da mặc định tối ưu cho AI phân biệt"""
    try:
        x, y, w, h = face_coords
        
        # Tạo bản sao để không thay đổi ảnh gốc
        normalized_image = image.copy()
        
        # Cắt vùng khuôn mặt với margin nhỏ
        margin = 0.1
        x_margin = int(w * margin)
        y_margin = int(h * margin)
        x1 = max(0, x - x_margin)
        y1 = max(0, y - y_margin)
        x2 = min(image.shape[1], x + w + x_margin)
        y2 = min(image.shape[0], y + h + y_margin)
        
        face_region = image[y1:y2, x1:x2].copy()
        
        if face_region.size == 0:
            return image
        
        # Chuyển sang HSV để dễ phân tích màu da
        hsv_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
        
        # Tạo mask cho vùng da (dựa trên khoảng màu da trong HSV)
        # Khoảng màu da trong HSV: H(0-25, 160-180), S(20-255), V(20-255)
        lower_skin1 = np.array([0, 20, 20], dtype=np.uint8)
        upper_skin1 = np.array([25, 255, 255], dtype=np.uint8)
        lower_skin2 = np.array([160, 20, 20], dtype=np.uint8)
        upper_skin2 = np.array([180, 255, 255], dtype=np.uint8)
        
        mask1 = cv2.inRange(hsv_face, lower_skin1, upper_skin1)
        mask2 = cv2.inRange(hsv_face, lower_skin2, upper_skin2)
        skin_mask = cv2.bitwise_or(mask1, mask2)
        
        # Làm mịn mask bằng morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
        
        # Nếu có facial landmarks từ InsightFace, sử dụng để cải thiện mask
        if face_obj is not None and hasattr(face_obj, 'kps') and face_obj.kps is not None:
            landmarks = face_obj.kps.astype(int)
            # Điều chỉnh landmarks về tọa độ trong face_region
            landmarks[:, 0] -= x1
            landmarks[:, 1] -= y1
            
            # Tạo mask từ landmarks (vùng tam giác giữa mắt và mũi)
            if len(landmarks) >= 3:
                # Lấy điểm giữa 2 mắt và mũi để tạo vùng da chính
                left_eye = landmarks[0]
                right_eye = landmarks[1] 
                nose = landmarks[2]
                
                # Tạo tam giác từ 3 điểm này
                triangle_points = np.array([left_eye, right_eye, nose], dtype=np.int32)
                landmark_mask = np.zeros(face_region.shape[:2], dtype=np.uint8)
                cv2.fillPoly(landmark_mask, [triangle_points], 255)
                
                # Kết hợp với skin mask
                skin_mask = cv2.bitwise_and(skin_mask, landmark_mask)
        
        # Kiểm tra có vùng da không
        if np.sum(skin_mask) == 0:
            print("Không tìm thấy vùng da, sử dụng ảnh gốc")
            return image
        
        # Định nghĩa màu da mặc định tối ưu cho AI (trong BGR)
        OPTIMAL_SKIN_COLOR_BGR = np.array([180, 160, 140], dtype=np.float32)  # Màu da trung tính
        TARGET_BRIGHTNESS = 160  # Độ sáng mục tiêu trong Lab color space
        
        print(f"Sử dụng màu da mặc định tối ưu BGR: {OPTIMAL_SKIN_COLOR_BGR}")
        
        # Chuyển sang Lab color space để xử lý độ sáng tốt hơn
        lab_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2LAB)
        l_channel = lab_face[:, :, 0].astype(np.float32)
        a_channel = lab_face[:, :, 1].astype(np.float32)
        b_channel = lab_face[:, :, 2].astype(np.float32)
        
        # Tạo mask mềm cho vùng da
        soft_mask = cv2.GaussianBlur(skin_mask.astype(np.float32), (15, 15), 0) / 255.0
        
        # Bước 1: Cân bằng độ sáng (Histogram Equalization cho vùng da)
        skin_l_values = l_channel[skin_mask > 0]
        if len(skin_l_values) > 0:
            # Tính toán adaptive brightness correction
            current_mean_brightness = np.mean(skin_l_values)
            current_std_brightness = np.std(skin_l_values)
            
            print(f"Độ sáng hiện tại: mean={current_mean_brightness:.1f}, std={current_std_brightness:.1f}")
            
            # Adaptive histogram equalization cho vùng da với thông số mạnh hơn
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(6,6))  # Tăng clipLimit và giảm tileGridSize
            
            # Áp dụng CLAHE chỉ cho vùng da
            l_channel_uint8 = l_channel.astype(np.uint8)
            l_equalized = clahe.apply(l_channel_uint8).astype(np.float32)
            
            # Tăng cường độ blend để CLAHE có hiệu quả mạnh hơn
            blend_strength = 0.9  # Tăng từ mặc định
            l_channel = l_channel * (1 - soft_mask * blend_strength) + l_equalized * (soft_mask * blend_strength)
            
            # Thêm bước làm mịn độ sáng bằng bilateral filter
            l_channel_smooth = cv2.bilateralFilter(l_channel.astype(np.uint8), 9, 75, 75).astype(np.float32)
            l_channel = l_channel * (1 - soft_mask * 0.5) + l_channel_smooth * (soft_mask * 0.5)
            
            # Điều chỉnh độ sáng trung bình về target với cường độ cao hơn
            skin_l_after_eq = l_channel[skin_mask > 0]
            new_mean_brightness = np.mean(skin_l_after_eq)
            brightness_adjustment = (TARGET_BRIGHTNESS - new_mean_brightness) * 1.2  # Tăng cường độ điều chỉnh
            
            # Áp dụng brightness adjustment với soft mask
            l_channel = l_channel + (brightness_adjustment * soft_mask)
            
            # Thêm bước cân bằng local contrast
            # Tính local mean và điều chỉnh từng vùng
            kernel_size = 15
            local_mean = cv2.GaussianBlur(l_channel, (kernel_size, kernel_size), 0)
            local_diff = l_channel - local_mean
            enhanced_l = local_mean + local_diff * 0.7  # Giảm local variation
            l_channel = l_channel * (1 - soft_mask * 0.6) + enhanced_l * (soft_mask * 0.6)
            
            print(f"Điều chỉnh độ sáng: {brightness_adjustment:.1f}")
        
        # Bước 2: Chuẩn hóa màu sắc (a, b channels)
        # Tính màu da trung bình hiện tại trong Lab
        skin_pixels_lab = np.stack([l_channel[skin_mask > 0], 
                                   a_channel[skin_mask > 0], 
                                   b_channel[skin_mask > 0]], axis=1)
        
        if len(skin_pixels_lab) > 0:
            mean_a = np.mean(skin_pixels_lab[:, 1])
            mean_b = np.mean(skin_pixels_lab[:, 2])
            
            # Chuyển optimal color sang Lab để lấy target a, b
            optimal_bgr_reshaped = OPTIMAL_SKIN_COLOR_BGR.reshape(1, 1, 3).astype(np.uint8)
            optimal_lab = cv2.cvtColor(optimal_bgr_reshaped, cv2.COLOR_BGR2LAB)[0, 0]
            target_a, target_b = optimal_lab[1], optimal_lab[2]
            
            # Điều chỉnh a, b channels với cường độ cao hơn
            a_adjustment = (target_a - mean_a) * 1.5  # Tăng cường độ điều chỉnh màu
            b_adjustment = (target_b - mean_b) * 1.5
            
            # Áp dụng điều chỉnh màu với cường độ cao
            a_channel = a_channel + (a_adjustment * soft_mask * 0.9)
            b_channel = b_channel + (b_adjustment * soft_mask * 0.9)
            
            # Thêm bước làm mịn màu sắc
            a_channel_smooth = cv2.GaussianBlur(a_channel.astype(np.uint8), (7, 7), 0).astype(np.float32)
            b_channel_smooth = cv2.GaussianBlur(b_channel.astype(np.uint8), (7, 7), 0).astype(np.float32)
            
            a_channel = a_channel * (1 - soft_mask * 0.3) + a_channel_smooth * (soft_mask * 0.3)
            b_channel = b_channel * (1 - soft_mask * 0.3) + b_channel_smooth * (soft_mask * 0.3)
            
            print(f"Điều chỉnh màu sắc: a={a_adjustment:.1f}, b={b_adjustment:.1f}")
        
        # Ghép lại các channel và chuyển về BGR
        l_channel = np.clip(l_channel, 0, 255)
        a_channel = np.clip(a_channel, 0, 255)
        b_channel = np.clip(b_channel, 0, 255)
        
        adjusted_lab = np.stack([l_channel.astype(np.uint8), 
                                a_channel.astype(np.uint8), 
                                b_channel.astype(np.uint8)], axis=2)
        
        adjusted_face = cv2.cvtColor(adjusted_lab, cv2.COLOR_LAB2BGR)
        
        # Áp dụng lại vào ảnh gốc
        normalized_image[y1:y2, x1:x2] = adjusted_face
        
        print(f"Đã chuẩn hóa màu da về tone mặc định cho vùng khuôn mặt {face_region.shape}")
        return normalized_image
        
    except Exception as e:
        print(f"Lỗi chuẩn hóa màu da: {str(e)}")
        return image

def extract_canny_feature_points(image: np.ndarray, face_obj, bbox: tuple) -> Optional[np.ndarray]:
    """Trích xuất các điểm đặc trưng từ khuôn mặt sử dụng Canny edge detection"""
    try:
        x, y, w, h = bbox
        
        # Crop face region với margin
        margin = 0.1
        x_margin = int(w * margin)
        y_margin = int(h * margin)
        x1 = max(0, x - x_margin)
        y1 = max(0, y - y_margin)
        x2 = min(image.shape[1], x + w + x_margin)
        y2 = min(image.shape[0], y + h + y_margin)
        
        face_region = image[y1:y2, x1:x2]
        
        if face_region.size == 0:
            return None
        
        # Chuyển về grayscale
        if len(face_region.shape) == 3:
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        else:
            gray_face = face_region.copy()
        
        # Resize về kích thước chuẩn để đảm bảo consistency
        standard_size = (200, 200)
        gray_face = cv2.resize(gray_face, standard_size)
        
        # Áp dụng Gaussian blur để giảm noise
        blurred = cv2.GaussianBlur(gray_face, (5, 5), 0)
        
        # Canny edge detection
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
        
        # Tìm contours từ edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Trích xuất feature points từ contours
        feature_points = []
        
        for contour in contours:
            # Chỉ lấy contours có kích thước hợp lý
            if cv2.contourArea(contour) > 20:
                # Approximate contour để giảm số điểm
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Thêm các điểm vào feature points
                for point in approx:
                    x_coord, y_coord = point[0]
                    # Normalize coordinates to 0-1 range
                    norm_x = x_coord / standard_size[0]
                    norm_y = y_coord / standard_size[1]
                    feature_points.append([norm_x, norm_y])
        
        # Giới hạn số lượng feature points để tránh quá tải
        max_points = 100
        if len(feature_points) > max_points:
            # Sắp xếp theo khoảng cách từ center và chọn những điểm quan trọng nhất
            center_x, center_y = 0.5, 0.5
            feature_points.sort(key=lambda p: abs(p[0] - center_x) + abs(p[1] - center_y))
            feature_points = feature_points[:max_points]
        
        if len(feature_points) < 10:
            print(f"Không đủ feature points: {len(feature_points)}")
            return None
        
        feature_array = np.array(feature_points, dtype=np.float32)
        print(f"Extracted {len(feature_points)} Canny feature points")
        
        return feature_array
        
    except Exception as e:
        print(f"Lỗi trích xuất Canny feature points: {str(e)}")
        return None

def compare_canny_features(features1: np.ndarray, features2: np.ndarray, threshold: float = 0.1) -> float:
    """So sánh độ tương đồng giữa hai tập hợp Canny feature points"""
    try:
        if features1 is None or features2 is None:
            return 0.0
        
        if len(features1) == 0 or len(features2) == 0:
            return 0.0
        
        # Sử dụng Hungarian algorithm để match các điểm gần nhất
        
        # Tính ma trận khoảng cách giữa tất cả các cặp điểm
        distances = cdist(features1, features2, metric='euclidean')
        
        # Tìm các cặp điểm có khoảng cách nhỏ nhất
        matched_pairs = 0
        total_distance = 0.0
        
        # Với mỗi điểm trong features1, tìm điểm gần nhất trong features2
        for i in range(len(features1)):
            min_dist_idx = np.argmin(distances[i])
            min_distance = distances[i][min_dist_idx]
            
            if min_distance <= threshold:
                matched_pairs += 1
                total_distance += min_distance
        
        if matched_pairs == 0:
            return 0.0
        
        # Tính similarity score
        avg_distance = total_distance / matched_pairs
        match_ratio = matched_pairs / max(len(features1), len(features2))
        
        # Similarity score kết hợp match ratio và average distance
        similarity = match_ratio * (1.0 - avg_distance / threshold)
        
        print(f"Feature comparison: {matched_pairs}/{len(features1)} matched, avg_dist={avg_distance:.4f}, similarity={similarity:.4f}")
        
        return max(0.0, min(1.0, similarity))
        
    except Exception as e:
        print(f"Lỗi so sánh Canny features: {str(e)}")
        return 0.0

def save_employee_canny_features(employee_id: int, features: np.ndarray):
    """Lưu Canny feature points của nhân viên"""
    try:
        # Tạo thư mục nếu chưa có
        features_dir = "employee_canny_features"
        os.makedirs(features_dir, exist_ok=True)
        
        # Lưu features dưới dạng numpy array
        features_file = os.path.join(features_dir, f"employee_{employee_id}_features.npy")
        np.save(features_file, features)
        
        print(f"Đã lưu {len(features)} Canny feature points cho employee {employee_id}")
        
    except Exception as e:
        print(f"Lỗi lưu Canny features: {str(e)}")

def load_employee_canny_features(employee_id: int) -> Optional[np.ndarray]:
    """Tải Canny feature points của nhân viên"""
    try:
        features_file = os.path.join("employee_canny_features", f"employee_{employee_id}_features.npy")
        
        if os.path.exists(features_file):
            features = np.load(features_file)
            print(f"Đã tải {len(features)} Canny feature points cho employee {employee_id}")
            return features
        else:
            print(f"Không tìm thấy Canny features cho employee {employee_id}")
            return None
        
    except Exception as e:
        print(f"Lỗi trích xuất face Canny features: {str(e)}")
        return None

def align_face_simple(image: np.ndarray, face_coords: tuple) -> np.ndarray:
    """Căn chỉnh khuôn mặt đơn giản bằng crop và resize"""
    try:
        x, y, w, h = face_coords
        
        # Mở rộng vùng khuôn mặt 15% để có context tốt hơn (giảm từ 20%)
        margin = 0.15
        x_margin = int(w * margin)
        y_margin = int(h * margin)
        
        # Tính toán vùng mở rộng
        x1 = max(0, x - x_margin)
        y1 = max(0, y - y_margin)
        x2 = min(image.shape[1], x + w + x_margin)
        y2 = min(image.shape[0], y + h + y_margin)
        
        # Cắt khuôn mặt với margin
        face_roi = image[y1:y2, x1:x2]
        
        # Resize về kích thước chuẩn 112x112 cho InsightFace
        aligned_face = cv2.resize(face_roi, (112, 112), interpolation=cv2.INTER_LINEAR)
        
        print(f"Face aligned (simple): {face_roi.shape} -> {aligned_face.shape}")
        return aligned_face
        
    except Exception as e:
        print(f"Lỗi căn chỉnh khuôn mặt đơn giản: {str(e)}")
        raise

def extract_face_embedding_enhanced(image: np.ndarray, face_info: tuple) -> Optional[np.ndarray]:
    """Bước 5: Trích xuất đặc trưng bằng ArcFace embedding với quy trình chuẩn"""
    try:
        print(f"Starting enhanced embedding extraction with face_info: {face_info[:4]}")
        
        # Sử dụng InsightFace để extract embedding
        app = _get_face_app()
        if app is None:
            print("InsightFace không khả dụng, fallback to old method")
            return None
        
        # Thử 1: Căn chỉnh khuôn mặt với contour-based extraction
        try:
            # Sử dụng face segmentation nếu có InsightFace object
            if len(face_info) > 4 and face_info[4] is not None:
                aligned_face = extract_face_with_segmentation(image, face_info[4], face_info[:4])
                print(f"Face extracted with segmentation: {aligned_face.shape}")
            else:
                aligned_face = align_face(image, face_info)
                print(f"Face aligned (standard): {aligned_face.shape}")
            
            # Chuyển về BGR cho InsightFace nếu cần
            if aligned_face.max() <= 1.0:
                bgr_face = (aligned_face * 255).astype(np.uint8)
            else:
                bgr_face = aligned_face.astype(np.uint8)
                
            if len(bgr_face.shape) == 3 and bgr_face.shape[2] == 3:
                # Kiểm tra xem có phải RGB không
                if np.mean(bgr_face[:, :, 0]) < np.mean(bgr_face[:, :, 2]):  # R < B suggests RGB
                    bgr_face = cv2.cvtColor(bgr_face, cv2.COLOR_RGB2BGR)
            
            # Extract embedding từ aligned face
            faces = app.get(bgr_face)
            
            if faces:
                # Chọn face có bbox lớn nhất
                face_obj = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                
                # Lấy normalized embedding
                embedding = face_obj.normed_embedding
                if embedding is not None:
                    # Đảm bảo embedding được normalize về unit length
                    embedding = np.asarray(embedding, dtype=np.float32)
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    
                    print(f"Enhanced embedding extracted successfully: shape={embedding.shape}, norm={np.linalg.norm(embedding):.3f}")
                    return embedding
        except Exception as align_error:
            print(f"Face alignment failed: {str(align_error)}")
        
        # Thử 2: Sử dụng contour-based extraction trực tiếp
        try:
            x, y, w, h = face_info[:4]
            face_obj = face_info[4] if len(face_info) > 4 else None
            
            # Chuyển image về BGR uint8 nếu cần
            if image.max() <= 1.0:
                bgr_image = (image * 255).astype(np.uint8)
            else:
                bgr_image = image.astype(np.uint8)
            
            if len(bgr_image.shape) == 3 and bgr_image.shape[2] == 3:
                if np.mean(bgr_image[:, :, 0]) < np.mean(bgr_image[:, :, 2]):
                    bgr_image = cv2.cvtColor(bgr_image, cv2.COLOR_RGB2BGR)
            
            # Sử dụng face segmentation nếu có face object
            if face_obj is not None:
                segmented_face = extract_face_with_segmentation(bgr_image, face_obj, (x, y, w, h))
                print(f"Segmented face extracted: {segmented_face.shape}")
                
                # Extract embedding từ segmented face
                faces = app.get(segmented_face)
                if faces:
                    face_obj_new = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                    embedding = face_obj_new.normed_embedding
                    if embedding is not None:
                        embedding = np.asarray(embedding, dtype=np.float32)
                        norm = np.linalg.norm(embedding)
                        if norm > 0:
                            embedding = embedding / norm
                        print(f"Segmentation embedding extracted: shape={embedding.shape}, norm={np.linalg.norm(embedding):.3f}")
                        return embedding
            
            # Fallback: crop thông thường
            margin = 0.1
            x_margin = int(w * margin)
            y_margin = int(h * margin)
            x1 = max(0, x - x_margin)
            y1 = max(0, y - y_margin)
            x2 = min(bgr_image.shape[1], x + w + x_margin)
            y2 = min(bgr_image.shape[0], y + h + y_margin)
            
            face_crop = bgr_image[y1:y2, x1:x2]
            print(f"Face cropped (fallback): {face_crop.shape}")
            
            faces = app.get(face_crop)
            if faces:
                face_obj_new = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                embedding = face_obj_new.normed_embedding
                if embedding is not None:
                    embedding = np.asarray(embedding, dtype=np.float32)
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    print(f"Fallback embedding extracted: shape={embedding.shape}, norm={np.linalg.norm(embedding):.3f}")
                    return embedding
        except Exception as segmentation_error:
            print(f"Face segmentation method failed: {str(segmentation_error)}")
        
        print("All enhanced embedding methods failed")
        return None
        
    except Exception as e:
        print(f"Lỗi trích xuất embedding enhanced: {str(e)}")
        return None

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


def extract_face_region_only(image: np.ndarray, face_info: tuple, margin_ratio: float = 0.1) -> np.ndarray:
    """Cắt chỉ vùng khuôn mặt với margin rất nhỏ - không bao gồm vai"""
    try:
        x, y, w, h = face_info[:4]
        
        # Tính margin rất nhỏ chỉ để đảm bảo không mất phần khuôn mặt
        x_margin = int(w * margin_ratio)
        y_margin = int(h * margin_ratio)
        
        # Tính toán vùng cắt với margin nhỏ
        x1 = max(0, x - x_margin)
        y1 = max(0, y - y_margin)
        x2 = min(image.shape[1], x + w + x_margin)
        y2 = min(image.shape[0], y + h + y_margin)
        
        # Cắt vùng khuôn mặt
        face_region = image[y1:y2, x1:x2]
        
        print(f"Face region extracted: original {image.shape} -> face region {face_region.shape}")
        print(f"Face bbox: ({x}, {y}, {w}, {h}) -> cropped region: ({x1}, {y1}, {x2-x1}, {y2-y1})")
        
        return face_region
        
    except Exception as e:
        print(f"Lỗi cắt vùng khuôn mặt: {str(e)}")
        raise

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

def compare_embeddings_enhanced(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Bước 6: So sánh độ tương đồng bằng cosine similarity chuẩn"""
    try:
        # Đảm bảo embeddings được normalize
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            print("Embedding có norm = 0")
            return -1.0
        
        emb1_normalized = embedding1 / norm1
        emb2_normalized = embedding2 / norm2
        
        # Tính cosine similarity
        cosine_sim = float(np.dot(emb1_normalized, emb2_normalized))
        
        # Clamp về range [-1, 1] để đảm bảo
        cosine_sim = np.clip(cosine_sim, -1.0, 1.0)
        
        print(f"Cosine similarity: {cosine_sim:.4f}")
        return cosine_sim
        
    except Exception as e:
        print(f"Lỗi so sánh embeddings: {str(e)}")
        return -1.0

def make_face_decision(similarity: float, threshold: float = 0.80) -> tuple:
    """Bước 7: Ra quyết định dựa trên threshold"""
    try:
        is_same_person = similarity >= threshold
        
        if is_same_person:
            confidence = similarity
            message = f"Cùng người (similarity: {similarity:.3f} >= {threshold})"
        else:
            confidence = similarity
            message = f"Khác người (similarity: {similarity:.3f} < {threshold})"
        
        print(f"Decision: {message}")
        return is_same_person, confidence, message
        
    except Exception as e:
        print(f"Lỗi ra quyết định: {str(e)}")
        return False, 0.0, f"Lỗi: {str(e)}"

def compare_faces_complete_workflow(image1: np.ndarray, image2: np.ndarray) -> dict:
    """Quy trình hoàn chỉnh so sánh 2 khuôn mặt theo chuẩn InsightFace + OpenCV"""
    try:
        print("=== BẮT ĐẦU QUY TRÌNH SO SÁNH KHUÔN MẶT ===")
        
        # Bước 2: Tiền xử lý ảnh
        print("Bước 2: Tiền xử lý ảnh...")
        _, processed_img1 = preprocess_image(image1)
        _, processed_img2 = preprocess_image(image2)
        
        # Bước 3: Phát hiện khuôn mặt
        print("Bước 3: Phát hiện khuôn mặt...")
        faces1 = detect_faces_insightface(processed_img1)
        faces2 = detect_faces_insightface(processed_img2)
        
        if len(faces1) == 0:
            return {"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh 1", "similarity": -1.0}
        
        if len(faces2) == 0:
            return {"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh 2", "similarity": -1.0}
        
        # Chọn khuôn mặt lớn nhất từ mỗi ảnh
        face1_info = max(faces1, key=lambda f: f[2] * f[3])  # w * h
        face2_info = max(faces2, key=lambda f: f[2] * f[3])
        
        # Bước 5: Trích xuất đặc trưng
        print("Bước 5: Trích xuất đặc trưng...")
        embedding1 = extract_face_embedding_enhanced(processed_img1, face1_info)
        embedding2 = extract_face_embedding_enhanced(processed_img2, face2_info)
        
        if embedding1 is None:
            return {"success": False, "message": "Không thể trích xuất embedding từ ảnh 1", "similarity": -1.0}
        
        if embedding2 is None:
            return {"success": False, "message": "Không thể trích xuất embedding từ ảnh 2", "similarity": -1.0}
        
        # Bước 6: So sánh độ tương đồng
        print("Bước 6: So sánh độ tương đồng...")
        similarity = compare_embeddings_enhanced(embedding1, embedding2)
        
        # Bước 7: Ra quyết định
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
        
        # Bước 2 & 3: Tiền xử lý và phát hiện khuôn mặt theo quy trình chuẩn
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
        
        # Bước 4: Áp dụng chuẩn hóa màu da trước khi trích xuất features
        face_info = faces[0]
        face_obj = face_info[4] if len(face_info) > 4 else None
        
        # Chuẩn hóa màu da trên ảnh gốc (không phải processed_image)
        normalized_image = normalize_skin_tone(image, face_info[:4], face_obj)
        
        # Tiền xử lý ảnh đã chuẩn hóa
        _, normalized_processed_image = preprocess_image(normalized_image)
        
        # Trích xuất Canny feature points từ ảnh đã chuẩn hóa
        current_features = extract_canny_feature_points(normalized_processed_image, face_obj, face_info[:4])
        
        # Kiểm tra xem nhân viên đã đăng ký Canny features chưa
        stored_features = load_employee_canny_features(employee_id)
        
        if stored_features is None:
            return {
                "success": False,
                "message": "Nhân viên chưa đăng ký khuôn mặt. Vui lòng đăng ký trước",
                "confidence": 0.0,
                "employee_id": employee_id
            }
        
        # So sánh Canny feature points
        similarity = compare_canny_features(current_features, stored_features, threshold=0.1)
        
        print(f"Canny feature comparison — similarity: {similarity:.3f}")
        
        # Threshold cho Canny feature similarity (có thể điều chỉnh)
        CANNY_THRESHOLD = 0.3
        
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
        
        # Phát hiện khuôn mặt trực tiếp trên ảnh gốc (không resize)
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
        
        # Bước 4: Áp dụng chuẩn hóa màu da trước khi trích xuất features
        face_info = faces[0]
        face_obj = face_info[4] if len(face_info) > 4 else None
        
        # Chuẩn hóa màu da trên ảnh gốc
        normalized_image = normalize_skin_tone(image, face_info[:4], face_obj)
        
        # Trích xuất Canny feature points từ ảnh đã chuẩn hóa
        canny_features = extract_canny_feature_points(normalized_image, face_obj, face_info[:4])
        
        if canny_features is None:
            return {
                "success": False,
                "message": "Không thể trích xuất đặc trưng khuôn mặt từ ảnh"
            }
        
        # Lưu Canny feature points
        save_employee_canny_features(employee_id, canny_features)
        
        # Cắt và lưu chỉ vùng khuôn mặt từ ảnh gốc (không phải ảnh đã resize)
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
        
        # Xóa Canny features
        features_path = os.path.join("employee_canny_features", f"employee_{employee_id}_features.npy")
        if os.path.exists(features_path):
            try:
                os.remove(features_path)
                deleted_files.append(f"employee_{employee_id}_features.npy")
                print(f"Deleted Canny features: {features_path}")
            except Exception as e:
                errors.append(f"Cannot delete Canny features: {str(e)}")
        
        # Xóa embedding (legacy - có thể bỏ sau)
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
                # Sử dụng quy trình chuẩn để tạo embedding
                _, processed_img = preprocess_image(img)
                faces = detect_faces_insightface(processed_img)
                emb = None
                if len(faces) > 0:
                    emb = extract_face_embedding_enhanced(processed_img, faces[0])
                if emb is None:
                    # Fallback với phương pháp cũ
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

@app.post("/face-recognition/compare")
async def compare_two_faces(
    face_image1: UploadFile = File(...),
    face_image2: UploadFile = File(...)
):
    """API endpoint để test quy trình so sánh 2 khuôn mặt hoàn chỉnh"""
    try:
        print("=== TESTING COMPLETE FACE COMPARISON WORKFLOW ===")
        
        # Xử lý 2 ảnh upload
        image1 = process_uploaded_image(face_image1)
        image2 = process_uploaded_image(face_image2)
        
        # Chạy quy trình so sánh hoàn chỉnh
        result = compare_faces_complete_workflow(image1, image2)
        
        return result
        
    except Exception as e:
        print(f"Error in compare_two_faces: {str(e)}")
        return {
            "success": False,
            "message": f"Lỗi xử lý: {str(e)}",
            "similarity": -1.0
        }

@app.get("/face-recognition/info")
async def get_api_info():
    """Thông tin về API và quy trình xử lý"""
    return {
        "api_name": "Face Recognition API",
        "version": "2.0.0",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)