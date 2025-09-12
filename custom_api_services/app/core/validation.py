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
        
        # Calculate average color of borders
        avg_color = np.mean(border_pixels, axis=0)
        
        # Convert from BGR to RGB for easier understanding
        avg_color_rgb = avg_color[::-1]  # BGR to RGB
        
        # Define white and blue colors in RGB
        white_rgb = np.array([255, 255, 255])
        blue_rgb = np.array([0, 0, 255])  # Pure blue
        light_blue_rgb = np.array([173, 216, 230])  # Light blue
        
        # Calculate Euclidean distance
        dist_to_white = np.linalg.norm(avg_color_rgb - white_rgb)
        dist_to_blue = np.linalg.norm(avg_color_rgb - blue_rgb)
        dist_to_light_blue = np.linalg.norm(avg_color_rgb - light_blue_rgb)
        
        # Acceptance thresholds (adjustable)
        if dist_to_white <= WHITE_THRESHOLD:
            return True, "Nền trắng"
        elif dist_to_blue <= BLUE_THRESHOLD or dist_to_light_blue <= BLUE_THRESHOLD:
            return True, "Nền xanh"
        else:
            return False, f"Màu nền không hợp lệ. Màu trung bình: RGB({avg_color_rgb[0]:.0f}, {avg_color_rgb[1]:.0f}, {avg_color_rgb[2]:.0f}). Yêu cầu nền trắng hoặc xanh."
            
    except Exception as e:
        return False, f"Lỗi kiểm tra màu nền: {str(e)}"
