"""
Image validation utilities for face recognition
"""
import cv2
import numpy as np
from typing import Tuple
from app.config import *

def validate_image_aspect_ratio(image: np.ndarray) -> Tuple[bool, str]:
    """Check image aspect ratio (3:4 or 4:6)"""
    try:
        height, width = image.shape[:2]
        
        # Calculate aspect ratio
        aspect_ratio = width / height
        
        # Check 3:4 ratio (0.75) with 5% tolerance
        if abs(aspect_ratio - ASPECT_RATIO_3_4) <= ASPECT_RATIO_TOLERANCE:
            return True, "3:4"
        
        # Check 4:6 ratio (2:3 = 0.667) with 5% tolerance
        if abs(aspect_ratio - ASPECT_RATIO_4_6) <= ASPECT_RATIO_TOLERANCE:
            return True, "4:6"
        
        return False, f"Tỉ lệ hiện tại: {aspect_ratio:.3f}. Yêu cầu tỉ lệ 3:4 (0.75) hoặc 4:6 (0.667)"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra tỉ lệ khung hình: {str(e)}"

def validate_background_color(image: np.ndarray) -> Tuple[bool, str]:
    """Check background color (white or blue)"""
    try:
        # Get pixels from image borders to determine background color
        height, width = image.shape[:2]
        
        # Get pixels from 4 edges of image
        border_pixels = []
        
        # Top and bottom edges
        border_pixels.extend(image[0, :].reshape(-1, 3))
        border_pixels.extend(image[height-1, :].reshape(-1, 3))
        
        # Left and right edges
        border_pixels.extend(image[:, 0].reshape(-1, 3))
        border_pixels.extend(image[:, width-1].reshape(-1, 3))
        
        border_pixels = np.array(border_pixels)
        
        # Calculate average color of borders for reporting (BGR -> RGB for readability)
        avg_color = np.mean(border_pixels, axis=0)
        avg_color_rgb = avg_color[::-1]

        # Convert border pixels to HSV for robust color classification
        # OpenCV HSV ranges: H in [0,179], S in [0,255], V in [0,255]
        bgr_pixels_u8 = np.array(border_pixels, dtype=np.uint8).reshape(-1, 1, 3)
        hsv_pixels = cv2.cvtColor(bgr_pixels_u8, cv2.COLOR_BGR2HSV).reshape(-1, 3)
        H = hsv_pixels[:, 0]
        S = hsv_pixels[:, 1]
        V = hsv_pixels[:, 2]

        # Heuristics for white and blue backgrounds (configurable via app.config)
        # Using constants: WHITE_S_MAX, WHITE_V_MIN, BLUE_H_MIN, BLUE_H_MAX, BLUE_S_MIN, BLUE_V_MIN, BG_RATIO_THRESHOLD

        is_white = (S <= WHITE_S_MAX) & (V >= WHITE_V_MIN)
        is_blue = (H >= BLUE_H_MIN) & (H <= BLUE_H_MAX) & (S >= BLUE_S_MIN) & (V >= BLUE_V_MIN)

        total = max(len(hsv_pixels), 1)
        white_ratio = float(np.sum(is_white)) / total
        blue_ratio = float(np.sum(is_blue)) / total

        if white_ratio >= BG_RATIO_THRESHOLD:
            return True, "Nền trắng"
        if blue_ratio >= BG_RATIO_THRESHOLD:
            return True, "Nền xanh"

        return False, (
            f"Màu nền không hợp lệ. Màu trung bình: RGB({avg_color_rgb[0]:.0f}, {avg_color_rgb[1]:.0f}, {avg_color_rgb[2]:.0f}). "
            f"White_ratio={white_ratio:.2f}, Blue_ratio={blue_ratio:.2f}. Yêu cầu nền trắng hoặc xanh."
        )
            
    except Exception as e:
        return False, f"Lỗi kiểm tra màu nền: {str(e)}"
