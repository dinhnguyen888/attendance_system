"""
Image processing utilities for face recognition
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from app.config import *

def process_uploaded_image(file) -> np.ndarray:
    """Process uploaded image file and convert to numpy array"""
    try:
        # Read file content
        image_bytes = file.file.read()
        print(f"Uploaded file size: {len(image_bytes)} bytes")
        print(f"Uploaded file content type: {file.content_type}")
        
        # Convert to numpy array and decode
        nparr = np.frombuffer(image_bytes, np.uint8)
        print(f"Numpy array shape: {nparr.shape}")
        
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Không thể decode ảnh từ file upload")
        
        print(f"Successfully decoded image, shape: {img.shape}")
        return img
        
    except Exception as e:
        print(f"Lỗi xử lý ảnh upload: {str(e)}")
        raise ValueError(f"Lỗi xử lý ảnh upload: {str(e)}")

def preprocess_image(image: np.ndarray, target_size: tuple = TARGET_SIZE) -> Tuple[np.ndarray, np.ndarray]:
    """Preprocess image according to InsightFace standards"""
    try:
        # Convert color space from BGR to RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
        
        # Resize image to appropriate size for detection
        resized = cv2.resize(rgb_image, target_size, interpolation=cv2.INTER_LINEAR)
        
        # Normalize pixel values to range [0,1]
        normalized = resized.astype(np.float32) / 255.0
        
        print(f"Preprocessed image: {image.shape} -> {resized.shape}, normalized to [0,1]")
        return normalized, resized
        
    except Exception as e:
        print(f"Lỗi tiền xử lý ảnh: {str(e)}")
        raise

def scale_image_to_standard(image: np.ndarray, target_width: int = TARGET_WIDTH) -> np.ndarray:
    """Scale image to standard size for optimal face detection"""
    try:
        height, width = image.shape[:2]
        
        # Calculate scale ratio based on target width
        scale_ratio = target_width / width
        
        # Calculate new height to maintain aspect ratio
        target_height = int(height * scale_ratio)
        
        # Resize image
        scaled_image = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
        
        print(f"Scaled image from {width}x{height} to {target_width}x{target_height}")
        return scaled_image
        
    except Exception as e:
        print(f"Lỗi khi scale ảnh: {str(e)}")
        return image  # Return original image if error occurs

def extract_face_region_only(image: np.ndarray, face_info: tuple, margin_ratio: float = 0.1) -> np.ndarray:
    """Extract only face region with small margin - excluding shoulders"""
    try:
        x, y, w, h = face_info[:4]
        
        # Calculate very small margin to ensure no face parts are lost
        x_margin = int(w * margin_ratio)
        y_margin = int(h * margin_ratio)
        
        # Calculate crop region with small margin
        x1 = max(0, x - x_margin)
        y1 = max(0, y - y_margin)
        x2 = min(image.shape[1], x + w + x_margin)
        y2 = min(image.shape[0], y + h + y_margin)
        
        # Crop face region
        face_region = image[y1:y2, x1:x2]
        
        print(f"Face region extracted: original {image.shape} -> face region {face_region.shape}")
        print(f"Face bbox: ({x}, {y}, {w}, {h}) -> cropped region: ({x1}, {y1}, {x2-x1}, {y2-y1})")
        
        return face_region
        
    except Exception as e:
        print(f"Lỗi cắt vùng khuôn mặt: {str(e)}")
        raise
