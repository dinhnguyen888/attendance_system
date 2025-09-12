#!/usr/bin/env python3
"""
Test script for the new Canny-based face recognition system
"""

import cv2
import numpy as np
import requests
import json
from pathlib import Path

# API base URL
API_BASE = "http://localhost:8000"

def test_canny_feature_extraction():
    """Test Canny feature extraction locally"""
    print("=== Testing Canny Feature Extraction ===")
    
    # Import the functions from main.py
    import sys
    sys.path.append('.')
    from main import extract_canny_feature_points, compare_canny_features
    
    # Create a simple test image
    test_image = np.ones((300, 300, 3), dtype=np.uint8) * 128
    
    # Draw some face-like features
    cv2.circle(test_image, (100, 120), 15, (0, 0, 0), -1)  # Left eye
    cv2.circle(test_image, (200, 120), 15, (0, 0, 0), -1)  # Right eye
    cv2.circle(test_image, (150, 160), 8, (0, 0, 0), -1)   # Nose
    cv2.ellipse(test_image, (150, 200), (30, 15), 0, 0, 180, (0, 0, 0), 2)  # Mouth
    
    # Test feature extraction
    bbox = (50, 50, 200, 200)  # x, y, w, h
    features = extract_canny_feature_points(test_image, None, bbox)
    
    if features is not None:
        print(f"✓ Successfully extracted {len(features)} Canny feature points")
        
        # Test feature comparison with itself (should be high similarity)
        similarity = compare_canny_features(features, features)
        print(f"✓ Self-comparison similarity: {similarity:.3f}")
        
        # Create a slightly different image for comparison
        test_image2 = test_image.copy()
        cv2.circle(test_image2, (105, 125), 15, (0, 0, 0), -1)  # Slightly moved left eye
        
        features2 = extract_canny_feature_points(test_image2, None, bbox)
        if features2 is not None:
            similarity2 = compare_canny_features(features, features2)
            print(f"✓ Similar image comparison: {similarity2:.3f}")
        
        return True
    else:
        print("✗ Failed to extract Canny features")
        return False

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n=== Testing API Endpoints ===")
    
    try:
        # Test health check
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            print("✓ API is running")
        else:
            print("✗ API health check failed")
            return False
            
        # Test info endpoint
        response = requests.get(f"{API_BASE}/face-recognition/info")
        if response.status_code == 200:
            info = response.json()
            print(f"✓ API Info: {info.get('version', 'Unknown')}")
        else:
            print("✗ API info endpoint failed")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"✗ API test failed: {str(e)}")
        return False

def create_test_image(filename: str):
    """Create a test face image"""
    # Create a white background image (3:4 aspect ratio)
    height, width = 400, 300
    image = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Draw a simple face
    center_x, center_y = width // 2, height // 2
    
    # Face outline (ellipse)
    cv2.ellipse(image, (center_x, center_y), (80, 100), 0, 0, 360, (200, 180, 160), -1)
    
    # Eyes
    cv2.circle(image, (center_x - 25, center_y - 30), 8, (0, 0, 0), -1)
    cv2.circle(image, (center_x + 25, center_y - 30), 8, (0, 0, 0), -1)
    
    # Nose
    cv2.circle(image, (center_x, center_y), 4, (150, 120, 100), -1)
    
    # Mouth
    cv2.ellipse(image, (center_x, center_y + 30), (20, 10), 0, 0, 180, (100, 50, 50), 2)
    
    # Add some noise/texture for better Canny detection
    noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
    image = cv2.addWeighted(image, 0.9, noise, 0.1, 0)
    
    cv2.imwrite(filename, image)
    print(f"Created test image: {filename}")
    return filename

def test_registration_and_verification():
    """Test registration and verification with the new Canny system"""
    print("\n=== Testing Registration and Verification ===")
    
    # Create test images
    test_image1 = create_test_image("test_face_1.jpg")
    test_image2 = create_test_image("test_face_2.jpg")  # Slightly different
    
    try:
        # Test registration
        print("Testing registration...")
        with open(test_image1, 'rb') as f:
            files = {'face_image': f}
            data = {'employee_id': 999, 'action': 'register'}
            response = requests.post(f"{API_BASE}/face-recognition/register", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✓ Registration successful")
            else:
                print(f"✗ Registration failed: {result.get('message')}")
                return False
        else:
            print(f"✗ Registration request failed: {response.status_code}")
            return False
        
        # Test verification with same image
        print("Testing verification with same image...")
        with open(test_image1, 'rb') as f:
            files = {'face_image': f}
            data = {'employee_id': 999, 'action': 'check-in'}
            response = requests.post(f"{API_BASE}/face-recognition/verify", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✓ Verification successful with confidence: {result.get('confidence', 0):.3f}")
            else:
                print(f"✗ Verification failed: {result.get('message')}")
        else:
            print(f"✗ Verification request failed: {response.status_code}")
        
        # Test verification with different image
        print("Testing verification with different image...")
        with open(test_image2, 'rb') as f:
            files = {'face_image': f}
            data = {'employee_id': 999, 'action': 'check-in'}
            response = requests.post(f"{API_BASE}/face-recognition/verify", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Different image verification: {result.get('success')} with confidence: {result.get('confidence', 0):.3f}")
        
        # Clean up test employee
        print("Cleaning up test data...")
        response = requests.delete(f"{API_BASE}/face-recognition/employee/999")
        if response.status_code == 200:
            print("✓ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ Registration/Verification test failed: {str(e)}")
        return False
    finally:
        # Clean up test images
        for img in [test_image1, test_image2]:
            try:
                Path(img).unlink()
            except:
                pass

def main():
    """Run all tests"""
    print("🔍 Testing New Canny-based Face Recognition System")
    print("=" * 50)
    
    # Test 1: Local feature extraction
    test1_passed = test_canny_feature_extraction()
    
    # Test 2: API endpoints
    test2_passed = test_api_endpoints()
    
    # Test 3: Full registration and verification flow
    test3_passed = False
    if test2_passed:
        test3_passed = test_registration_and_verification()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Feature Extraction: {'✓ PASS' if test1_passed else '✗ FAIL'}")
    print(f"API Endpoints: {'✓ PASS' if test2_passed else '✗ FAIL'}")
    print(f"Registration/Verification: {'✓ PASS' if test3_passed else '✗ FAIL'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 All tests passed! Canny-based face recognition system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
