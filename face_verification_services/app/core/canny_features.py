"""
Canny edge detection feature extraction and comparison
"""
import cv2
import numpy as np
from typing import Optional
from scipy.spatial.distance import cdist
import os
from app.config import EMPLOYEE_CANNY_FEATURES_DIR

def extract_canny_feature_points(image: np.ndarray, face_obj, bbox: tuple) -> Optional[np.ndarray]:
    """Extract feature points from face using Canny edge detection"""
    try:
        x, y, w, h = bbox
        
        # Crop face region with margin
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
        
        # Convert to grayscale
        if len(face_region.shape) == 3:
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        else:
            gray_face = face_region.copy()
        
        # Resize to standard size for consistency
        standard_size = (200, 200)
        gray_face = cv2.resize(gray_face, standard_size)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray_face, (5, 5), 0)
        
        # Canny edge detection
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
        
        # Find contours from edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Extract feature points from contours
        feature_points = []
        
        for contour in contours:
            # Only take contours with reasonable size
            if cv2.contourArea(contour) > 20:
                # Approximate contour to reduce number of points
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Add points to feature points
                for point in approx:
                    x_coord, y_coord = point[0]
                    # Normalize coordinates to 0-1 range
                    norm_x = x_coord / standard_size[0]
                    norm_y = y_coord / standard_size[1]
                    feature_points.append([norm_x, norm_y])
        
        # Limit number of feature points to avoid overload
        max_points = 100
        if len(feature_points) > max_points:
            # Sort by distance from center and choose most important points
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
    """Compare similarity between two sets of Canny feature points"""
    try:
        if features1 is None or features2 is None:
            return 0.0
        
        if len(features1) == 0 or len(features2) == 0:
            return 0.0
        
        # Use Hungarian algorithm to match closest points
        
        # Calculate distance matrix between all point pairs
        distances = cdist(features1, features2, metric='euclidean')
        
        # Find pairs of points with minimum distance
        matched_pairs = 0
        total_distance = 0.0
        
        # For each point in features1, find closest point in features2
        for i in range(len(features1)):
            min_dist_idx = np.argmin(distances[i])
            min_distance = distances[i][min_dist_idx]
            
            if min_distance <= threshold:
                matched_pairs += 1
                total_distance += min_distance
        
        if matched_pairs == 0:
            return 0.0
        
        # Calculate similarity score
        avg_distance = total_distance / matched_pairs
        match_ratio = matched_pairs / max(len(features1), len(features2))
        
        # Similarity score combining match ratio and average distance
        similarity = match_ratio * (1.0 - avg_distance / threshold)
        
        print(f"Feature comparison: {matched_pairs}/{len(features1)} matched, avg_dist={avg_distance:.4f}, similarity={similarity:.4f}")
        
        return max(0.0, min(1.0, similarity))
        
    except Exception as e:
        print(f"Lỗi so sánh Canny features: {str(e)}")
        return 0.0

def save_employee_canny_features(employee_id: int, features: np.ndarray):
    """Save employee's Canny feature points"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(EMPLOYEE_CANNY_FEATURES_DIR, exist_ok=True)
        
        # Save features as numpy array
        features_file = os.path.join(EMPLOYEE_CANNY_FEATURES_DIR, f"employee_{employee_id}_features.npy")
        np.save(features_file, features)
        
        print(f"Đã lưu {len(features)} Canny feature points cho employee {employee_id}")
        
    except Exception as e:
        print(f"Lỗi lưu Canny features: {str(e)}")

def load_employee_canny_features(employee_id: int) -> Optional[np.ndarray]:
    """Load employee's Canny feature points"""
    try:
        features_file = os.path.join(EMPLOYEE_CANNY_FEATURES_DIR, f"employee_{employee_id}_features.npy")
        
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
