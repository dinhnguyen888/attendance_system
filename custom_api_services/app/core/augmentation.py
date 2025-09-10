"""
Image augmentation for face enrollment from 3x4 photos
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any
import random

def rotate_face(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate face image by given angle (degrees)"""
    try:
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Get rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Apply rotation
        rotated = cv2.warpAffine(image, rotation_matrix, (w, h), 
                                flags=cv2.INTER_LINEAR, 
                                borderMode=cv2.BORDER_REFLECT)
        
        return rotated
    except Exception as e:
        print(f"Error rotating face: {str(e)}")
        return image

def adjust_lighting(image: np.ndarray, gamma: float) -> np.ndarray:
    """Adjust lighting using gamma correction"""
    try:
        # Build lookup table for gamma correction
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 
                         for i in np.arange(0, 256)]).astype("uint8")
        
        # Apply gamma correction
        adjusted = cv2.LUT(image, table)
        return adjusted
    except Exception as e:
        print(f"Error adjusting lighting: {str(e)}")
        return image

def apply_blur(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Apply Gaussian blur"""
    try:
        blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        return blurred
    except Exception as e:
        print(f"Error applying blur: {str(e)}")
        return image

def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Enhance contrast using CLAHE"""
    try:
        if len(image.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge channels and convert back
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        else:
            # Grayscale image
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
        
        return enhanced
    except Exception as e:
        print(f"Error enhancing contrast: {str(e)}")
        return image

def generate_augmented_faces(face_image: np.ndarray, num_augmentations: int = 8) -> List[np.ndarray]:
    """Generate multiple augmented versions of a face image"""
    augmented_faces = []
    
    try:
        # Original image (enhanced)
        original_enhanced = enhance_contrast(face_image)
        augmented_faces.append(original_enhanced)
        
        # Generate augmentations
        for i in range(num_augmentations - 1):
            augmented = face_image.copy()
            
            # Random rotation (-15 to +15 degrees)
            if random.random() > 0.3:  # 70% chance
                angle = random.uniform(-15, 15)
                augmented = rotate_face(augmented, angle)
            
            # Random lighting adjustment (gamma 0.8 to 1.2)
            if random.random() > 0.2:  # 80% chance
                gamma = random.uniform(0.8, 1.2)
                augmented = adjust_lighting(augmented, gamma)
            
            # Random blur (30% chance)
            if random.random() > 0.7:
                kernel_size = random.choice([3, 5])
                augmented = apply_blur(augmented, kernel_size)
            
            # Contrast enhancement (50% chance)
            if random.random() > 0.5:
                augmented = enhance_contrast(augmented)
            
            augmented_faces.append(augmented)
        
        print(f"Generated {len(augmented_faces)} augmented face variations")
        return augmented_faces
        
    except Exception as e:
        print(f"Error generating augmented faces: {str(e)}")
        return [face_image]  # Return original if augmentation fails

def assess_face_quality(face_image: np.ndarray) -> Tuple[float, dict]:
    """Assess face image quality (blur, pose, lighting)"""
    try:
        quality_score = 0.0
        metrics = {}
        
        # Convert to grayscale for analysis
        if len(face_image.shape) == 3:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_image
        
        # 1. Blur assessment (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(laplacian_var / 500.0, 1.0)  # Normalize to 0-1
        metrics['blur_score'] = blur_score
        
        # 2. Brightness assessment
        brightness = np.mean(gray)
        brightness_score = 1.0 - abs(brightness - 128) / 128.0  # Optimal around 128
        metrics['brightness_score'] = brightness_score
        
        # 3. Contrast assessment
        contrast = gray.std()
        contrast_score = min(contrast / 64.0, 1.0)  # Normalize to 0-1
        metrics['contrast_score'] = contrast_score
        
        # 4. Face size assessment (assume face should be at least 80x80)
        h, w = gray.shape
        size_score = min(min(h, w) / 80.0, 1.0)
        metrics['size_score'] = size_score
        
        # Overall quality score (weighted average)
        quality_score = (
            0.3 * blur_score +
            0.2 * brightness_score +
            0.3 * contrast_score +
            0.2 * size_score
        )
        
        metrics['overall_quality'] = quality_score
        
        return quality_score, metrics
        
    except Exception as e:
        print(f"Error assessing face quality: {str(e)}")
        return 0.5, {'error': str(e)}

def preprocess_webcam_frame(frame: np.ndarray) -> Tuple[np.ndarray, float, dict]:
    """Preprocess webcam frame for face recognition"""
    try:
        processed_frame = frame.copy()
        
        # 1. Assess quality first
        quality_score, quality_metrics = assess_face_quality(processed_frame)
        
        # 2. If quality is too low, return early
        if quality_score < 0.3:
            return processed_frame, quality_score, quality_metrics
        
        # 3. Normalize lighting with CLAHE
        processed_frame = enhance_contrast(processed_frame)
        
        # 4. Gamma correction if too dark or bright
        brightness = np.mean(cv2.cvtColor(processed_frame, cv2.COLOR_BGR2GRAY))
        if brightness < 100:
            # Too dark, brighten
            processed_frame = adjust_lighting(processed_frame, 0.8)
        elif brightness > 180:
            # Too bright, darken
            processed_frame = adjust_lighting(processed_frame, 1.2)
        
        # 5. Reassess quality after preprocessing
        final_quality, final_metrics = assess_face_quality(processed_frame)
        
        return processed_frame, final_quality, final_metrics
        
    except Exception as e:
        print(f"Error preprocessing webcam frame: {str(e)}")
        return frame, 0.0, {'error': str(e)}
