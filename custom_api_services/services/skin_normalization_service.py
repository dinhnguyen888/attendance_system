"""
Skin tone normalization service for face recognition API
"""
import cv2
import numpy as np
from typing import Optional
from models.config import *

def normalize_skin_tone(image: np.ndarray, face_coords: tuple, face_obj=None) -> np.ndarray:
    """Normalize face skin tone to optimal default color for AI discrimination"""
    try:
        x, y, w, h = face_coords
        
        # Create copy to not modify original image
        normalized_image = image.copy()
        
        # Crop face region with small margin
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
        
        # Convert to HSV for easier skin color analysis
        hsv_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
        
        # Create mask for skin regions (based on skin color range in HSV)
        # Skin color range in HSV: H(0-25, 160-180), S(20-255), V(20-255)
        lower_skin1 = np.array([0, 20, 20], dtype=np.uint8)
        upper_skin1 = np.array([25, 255, 255], dtype=np.uint8)
        lower_skin2 = np.array([160, 20, 20], dtype=np.uint8)
        upper_skin2 = np.array([180, 255, 255], dtype=np.uint8)
        
        mask1 = cv2.inRange(hsv_face, lower_skin1, upper_skin1)
        mask2 = cv2.inRange(hsv_face, lower_skin2, upper_skin2)
        skin_mask = cv2.bitwise_or(mask1, mask2)
        
        # Smooth mask using morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
        
        # If we have facial landmarks from InsightFace, use them to improve mask
        if face_obj is not None and hasattr(face_obj, 'kps') and face_obj.kps is not None:
            landmarks = face_obj.kps.astype(int)
            # Adjust landmarks to face_region coordinates
            landmarks[:, 0] -= x1
            landmarks[:, 1] -= y1
            
            # Create mask from landmarks (triangle area between eyes and nose)
            if len(landmarks) >= 3:
                # Get points between 2 eyes and nose to create main skin area
                left_eye = landmarks[0]
                right_eye = landmarks[1] 
                nose = landmarks[2]
                
                # Create triangle from these 3 points
                triangle_points = np.array([left_eye, right_eye, nose], dtype=np.int32)
                landmark_mask = np.zeros(face_region.shape[:2], dtype=np.uint8)
                cv2.fillPoly(landmark_mask, [triangle_points], 255)
                
                # Combine with skin mask
                skin_mask = cv2.bitwise_and(skin_mask, landmark_mask)
        
        # Check if we have skin regions
        if np.sum(skin_mask) == 0:
            print("Không tìm thấy vùng da, sử dụng ảnh gốc")
            return image
        
        # Define optimal default skin color for AI (in BGR)
        optimal_skin_color_bgr = np.array(OPTIMAL_SKIN_COLOR_BGR, dtype=np.float32)
        target_brightness = TARGET_BRIGHTNESS
        
        print(f"Sử dụng màu da mặc định tối ưu BGR: {optimal_skin_color_bgr}")
        
        # Convert to Lab color space for better brightness processing
        lab_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2LAB)
        l_channel = lab_face[:, :, 0].astype(np.float32)
        a_channel = lab_face[:, :, 1].astype(np.float32)
        b_channel = lab_face[:, :, 2].astype(np.float32)
        
        # Create soft mask for skin regions
        soft_mask = cv2.GaussianBlur(skin_mask.astype(np.float32), (15, 15), 0) / 255.0
        
        # Step 1: Balance brightness (Histogram Equalization for skin regions)
        skin_l_values = l_channel[skin_mask > 0]
        if len(skin_l_values) > 0:
            # Calculate adaptive brightness correction
            current_mean_brightness = np.mean(skin_l_values)
            current_std_brightness = np.std(skin_l_values)
            
            print(f"Độ sáng hiện tại: mean={current_mean_brightness:.1f}, std={current_std_brightness:.1f}")
            
            # Adaptive histogram equalization for skin regions with stronger parameters
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(6,6))
            
            # Apply CLAHE only to skin regions
            l_channel_uint8 = l_channel.astype(np.uint8)
            l_equalized = clahe.apply(l_channel_uint8).astype(np.float32)
            
            # Increase blend strength for stronger CLAHE effect
            blend_strength = 0.9
            l_channel = l_channel * (1 - soft_mask * blend_strength) + l_equalized * (soft_mask * blend_strength)
            
            # Add brightness smoothing step using bilateral filter
            l_channel_smooth = cv2.bilateralFilter(l_channel.astype(np.uint8), 9, 75, 75).astype(np.float32)
            l_channel = l_channel * (1 - soft_mask * 0.5) + l_channel_smooth * (soft_mask * 0.5)
            
            # Adjust average brightness to target with higher intensity
            skin_l_after_eq = l_channel[skin_mask > 0]
            new_mean_brightness = np.mean(skin_l_after_eq)
            brightness_adjustment = (target_brightness - new_mean_brightness) * 1.2
            
            # Apply brightness adjustment with soft mask
            l_channel = l_channel + (brightness_adjustment * soft_mask)
            
            # Add local contrast balancing step
            kernel_size = 15
            local_mean = cv2.GaussianBlur(l_channel, (kernel_size, kernel_size), 0)
            local_diff = l_channel - local_mean
            enhanced_l = local_mean + local_diff * 0.7
            l_channel = l_channel * (1 - soft_mask * 0.6) + enhanced_l * (soft_mask * 0.6)
            
            print(f"Điều chỉnh độ sáng: {brightness_adjustment:.1f}")
        
        # Step 2: Normalize color (a, b channels)
        skin_pixels_lab = np.stack([l_channel[skin_mask > 0], 
                                   a_channel[skin_mask > 0], 
                                   b_channel[skin_mask > 0]], axis=1)
        
        if len(skin_pixels_lab) > 0:
            mean_a = np.mean(skin_pixels_lab[:, 1])
            mean_b = np.mean(skin_pixels_lab[:, 2])
            
            # Convert optimal color to Lab to get target a, b
            optimal_bgr_reshaped = optimal_skin_color_bgr.reshape(1, 1, 3).astype(np.uint8)
            optimal_lab = cv2.cvtColor(optimal_bgr_reshaped, cv2.COLOR_BGR2LAB)[0, 0]
            target_a, target_b = optimal_lab[1], optimal_lab[2]
            
            # Adjust a, b channels with higher intensity
            a_adjustment = (target_a - mean_a) * 1.5
            b_adjustment = (target_b - mean_b) * 1.5
            
            # Apply color adjustment with high intensity
            a_channel = a_channel + (a_adjustment * soft_mask * 0.9)
            b_channel = b_channel + (b_adjustment * soft_mask * 0.9)
            
            # Add color smoothing step
            a_channel_smooth = cv2.GaussianBlur(a_channel.astype(np.uint8), (7, 7), 0).astype(np.float32)
            b_channel_smooth = cv2.GaussianBlur(b_channel.astype(np.uint8), (7, 7), 0).astype(np.float32)
            
            a_channel = a_channel * (1 - soft_mask * 0.3) + a_channel_smooth * (soft_mask * 0.3)
            b_channel = b_channel * (1 - soft_mask * 0.3) + b_channel_smooth * (soft_mask * 0.3)
            
            print(f"Điều chỉnh màu sắc: a={a_adjustment:.1f}, b={b_adjustment:.1f}")
        
        # Merge channels and convert back to BGR
        l_channel = np.clip(l_channel, 0, 255)
        a_channel = np.clip(a_channel, 0, 255)
        b_channel = np.clip(b_channel, 0, 255)
        
        adjusted_lab = np.stack([l_channel.astype(np.uint8), 
                                a_channel.astype(np.uint8), 
                                b_channel.astype(np.uint8)], axis=2)
        
        adjusted_face = cv2.cvtColor(adjusted_lab, cv2.COLOR_LAB2BGR)
        
        # Apply back to original image
        normalized_image[y1:y2, x1:x2] = adjusted_face
        
        print(f"Đã chuẩn hóa màu da về tone mặc định cho vùng khuôn mặt {face_region.shape}")
        return normalized_image
        
    except Exception as e:
        print(f"Lỗi chuẩn hóa màu da: {str(e)}")
        return image
