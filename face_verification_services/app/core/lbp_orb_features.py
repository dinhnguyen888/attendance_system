"""
LBP (Local Binary Patterns) + ORB features extraction as backup method
"""
import cv2
import numpy as np
from typing import Optional, Tuple
from skimage.feature import local_binary_pattern
from skimage import exposure

def extract_lbp_features(image: np.ndarray, face_coords: tuple) -> Optional[np.ndarray]:
    """Extract LBP (Local Binary Pattern) features from face region"""
    try:
        x, y, w, h = face_coords
        
        # Extract face region with margin
        margin = 0.1
        x_margin = int(w * margin)
        y_margin = int(h * margin)
        x1 = max(0, x - x_margin)
        y1 = max(0, y - y_margin)
        x2 = min(image.shape[1], x + w + x_margin)
        y2 = min(image.shape[0], y + h + y_margin)
        
        face_region = image[y1:y2, x1:x2]
        
        # Convert to grayscale if needed
        if len(face_region.shape) == 3:
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        else:
            gray_face = face_region
        
        # Resize to standard size
        gray_face = cv2.resize(gray_face, (128, 128))
        
        # Apply histogram equalization
        gray_face = cv2.equalizeHist(gray_face)
        
        # Extract LBP features
        radius = 3
        n_points = 8 * radius
        lbp = local_binary_pattern(gray_face, n_points, radius, method='uniform')
        
        # Calculate histogram
        n_bins = n_points + 2
        hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins), density=True)
        
        # Normalize histogram
        hist = hist.astype(np.float32)
        norm = np.linalg.norm(hist)
        if norm > 0:
            hist = hist / norm
        
        print(f"LBP features extracted: shape={hist.shape}, norm={np.linalg.norm(hist):.3f}")
        return hist
        
    except Exception as e:
        print(f"Error extracting LBP features: {str(e)}")
        return None

def extract_orb_features(image: np.ndarray, face_coords: tuple) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Extract ORB (Oriented FAST and Rotated BRIEF) features from face region"""
    try:
        x, y, w, h = face_coords
        
        # Extract face region with margin
        margin = 0.15
        x_margin = int(w * margin)
        y_margin = int(h * margin)
        x1 = max(0, x - x_margin)
        y1 = max(0, y - y_margin)
        x2 = min(image.shape[1], x + w + x_margin)
        y2 = min(image.shape[0], y + h + y_margin)
        
        face_region = image[y1:y2, x1:x2]
        
        # Convert to grayscale if needed
        if len(face_region.shape) == 3:
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        else:
            gray_face = face_region
        
        # Resize to standard size
        gray_face = cv2.resize(gray_face, (256, 256))
        
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray_face = clahe.apply(gray_face)
        
        # Initialize ORB detector
        orb = cv2.ORB_create(nfeatures=1000, scaleFactor=1.2, nlevels=8)
        
        # Detect keypoints and compute descriptors
        keypoints, descriptors = orb.detectAndCompute(gray_face, None)
        
        if descriptors is None or len(descriptors) == 0:
            print("No ORB features detected")
            return None
        
        # Convert keypoints to array format
        kp_array = np.array([[kp.pt[0], kp.pt[1], kp.angle, kp.response] for kp in keypoints])
        
        print(f"ORB features extracted: {len(keypoints)} keypoints, {descriptors.shape} descriptors")
        return kp_array, descriptors
        
    except Exception as e:
        print(f"Error extracting ORB features: {str(e)}")
        return None

def extract_lbp_orb_combined(image: np.ndarray, face_coords: tuple) -> Optional[dict]:
    """Extract both LBP and ORB features and combine them"""
    try:
        # Extract LBP features
        lbp_features = extract_lbp_features(image, face_coords)
        
        # Extract ORB features
        orb_result = extract_orb_features(image, face_coords)
        
        if lbp_features is None and orb_result is None:
            return None
        
        result = {}
        
        if lbp_features is not None:
            result['lbp'] = lbp_features
        
        if orb_result is not None:
            result['orb_keypoints'] = orb_result[0]
            result['orb_descriptors'] = orb_result[1]
        
        print(f"LBP+ORB combined features extracted successfully")
        return result
        
    except Exception as e:
        print(f"Error extracting LBP+ORB combined features: {str(e)}")
        return None

def compare_lbp_features(lbp1: np.ndarray, lbp2: np.ndarray) -> float:
    """Compare LBP features using chi-square distance"""
    try:
        # Chi-square distance
        chi2_dist = 0.5 * np.sum(((lbp1 - lbp2) ** 2) / (lbp1 + lbp2 + 1e-10))
        
        # Convert to similarity (0-1 range)
        similarity = np.exp(-chi2_dist)
        
        print(f"LBP similarity: {similarity:.4f}")
        return float(similarity)
        
    except Exception as e:
        print(f"Error comparing LBP features: {str(e)}")
        return 0.0

def compare_orb_features(desc1: np.ndarray, desc2: np.ndarray) -> float:
    """Compare ORB descriptors using BFMatcher"""
    try:
        if desc1 is None or desc2 is None or len(desc1) == 0 or len(desc2) == 0:
            return 0.0
        
        # Use BFMatcher with Hamming distance for binary descriptors
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(desc1, desc2)
        
        if len(matches) == 0:
            return 0.0
        
        # Sort matches by distance
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Calculate similarity based on good matches
        good_matches = [m for m in matches if m.distance < 50]  # Threshold for good matches
        
        if len(good_matches) == 0:
            return 0.0
        
        # Similarity based on ratio of good matches and average distance
        match_ratio = len(good_matches) / min(len(desc1), len(desc2))
        avg_distance = np.mean([m.distance for m in good_matches])
        
        # Normalize distance (0-64 for Hamming distance with 256-bit descriptors)
        normalized_distance = 1.0 - (avg_distance / 64.0)
        
        similarity = match_ratio * normalized_distance
        
        print(f"ORB similarity: {similarity:.4f} (good matches: {len(good_matches)}/{len(matches)})")
        return float(np.clip(similarity, 0.0, 1.0))
        
    except Exception as e:
        print(f"Error comparing ORB features: {str(e)}")
        return 0.0

def compare_lbp_orb_combined(features1: dict, features2: dict) -> float:
    """Compare combined LBP+ORB features"""
    try:
        lbp_similarity = 0.0
        orb_similarity = 0.0
        
        # Compare LBP features if available
        if 'lbp' in features1 and 'lbp' in features2:
            lbp_similarity = compare_lbp_features(features1['lbp'], features2['lbp'])
        
        # Compare ORB features if available
        if 'orb_descriptors' in features1 and 'orb_descriptors' in features2:
            orb_similarity = compare_orb_features(features1['orb_descriptors'], features2['orb_descriptors'])
        
        # Combined similarity: 60% LBP + 40% ORB
        if lbp_similarity > 0 and orb_similarity > 0:
            combined_similarity = 0.6 * lbp_similarity + 0.4 * orb_similarity
            method = "LBP+ORB"
        elif lbp_similarity > 0:
            combined_similarity = lbp_similarity
            method = "LBP only"
        elif orb_similarity > 0:
            combined_similarity = orb_similarity
            method = "ORB only"
        else:
            combined_similarity = 0.0
            method = "No features"
        
        print(f"Combined {method} similarity: {combined_similarity:.4f}")
        return float(combined_similarity)
        
    except Exception as e:
        print(f"Error comparing LBP+ORB combined features: {str(e)}")
        return 0.0
