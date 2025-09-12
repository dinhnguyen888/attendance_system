#!/usr/bin/env python3
"""
Test script for enhanced face registration with sketch detection and face cropping
"""

import requests
import cv2
import numpy as np
import os
import base64
from io import BytesIO

API_BASE_URL = "http://localhost:8000"

def create_test_sketch_image():
    """Tạo ảnh sketch để test sketch detection"""
    # Tạo ảnh trắng
    img = np.ones((480, 360, 3), dtype=np.uint8) * 255
    
    # Vẽ một khuôn mặt đơn giản bằng đường line
    # Vẽ hình tròn cho mặt
    cv2.circle(img, (180, 200), 80, (0, 0, 0), 2)
    
    # Vẽ mắt
    cv2.circle(img, (160, 180), 10, (0, 0, 0), -1)
    cv2.circle(img, (200, 180), 10, (0, 0, 0), -1)
    
    # Vẽ mũi
    cv2.line(img, (180, 190), (180, 210), (0, 0, 0), 2)
    
    # Vẽ miệng
    cv2.ellipse(img, (180, 230), (20, 10), 0, 0, 180, (0, 0, 0), 2)
    
    return img

def create_test_real_image():
    """Tạo ảnh giả lập ảnh thật với noise và texture"""
    # Tạo ảnh với noise
    img = np.random.randint(100, 200, (480, 360, 3), dtype=np.uint8)
    
    # Thêm gradient để giả lập ánh sáng
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            factor = 0.8 + 0.4 * (i / img.shape[0])
            img[i, j] = np.clip(img[i, j] * factor, 0, 255)
    
    # Thêm một vùng tối hơn ở giữa để giả lập khuôn mặt
    cv2.ellipse(img, (180, 240), (60, 80), 0, 0, 360, (80, 90, 100), -1)
    
    return img

def test_sketch_detection():
    """Test sketch detection functionality"""
    print("=== Testing Sketch Detection ===")
    
    # Test với ảnh sketch
    sketch_img = create_test_sketch_image()
    cv2.imwrite("test_sketch.jpg", sketch_img)
    
    try:
        with open("test_sketch.jpg", "rb") as f:
            files = {"face_image": ("test_sketch.jpg", f, "image/jpeg")}
            data = {"employee_id": 9999, "action": "register"}
            
            response = requests.post(f"{API_BASE_URL}/face-recognition/register", 
                                   files=files, data=data)
            result = response.json()
            
            print(f"Sketch image test result: {result}")
            
            if result.get("success") == False and "sketch" in result.get("message", "").lower():
                print("✅ Sketch detection working correctly - rejected sketch image")
            else:
                print("❌ Sketch detection failed - should have rejected sketch image")
                
    except Exception as e:
        print(f"❌ Error testing sketch detection: {e}")
    
    # Cleanup
    if os.path.exists("test_sketch.jpg"):
        os.remove("test_sketch.jpg")

def test_api_health():
    """Test API health endpoint"""
    print("=== Testing API Health ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/face-recognition/health")
        result = response.json()
        
        print(f"API Health: {result}")
        
        if result.get("status") == "healthy":
            print("✅ API is healthy")
            return True
        else:
            print("❌ API is not healthy")
            return False
            
    except Exception as e:
        print(f"❌ Error checking API health: {e}")
        return False

def test_face_cropping():
    """Test face cropping by checking saved face images"""
    print("=== Testing Face Cropping ===")
    
    # Tạo ảnh test với khuôn mặt giả
    real_img = create_test_real_image()
    cv2.imwrite("test_real.jpg", real_img)
    
    try:
        with open("test_real.jpg", "rb") as f:
            files = {"face_image": ("test_real.jpg", f, "image/jpeg")}
            data = {"employee_id": 9998, "action": "register"}
            
            response = requests.post(f"{API_BASE_URL}/face-recognition/register", 
                                   files=files, data=data)
            result = response.json()
            
            print(f"Real image registration result: {result}")
            
            # Kiểm tra xem có file face được lưu không
            face_file = "employee_faces/employee_9998.jpg"
            if os.path.exists(face_file):
                saved_face = cv2.imread(face_file)
                if saved_face is not None:
                    print(f"✅ Face cropping working - saved face size: {saved_face.shape}")
                    
                    # Kiểm tra kích thước - should be smaller than original
                    if saved_face.shape[0] < real_img.shape[0] and saved_face.shape[1] < real_img.shape[1]:
                        print("✅ Face was properly cropped (smaller than original)")
                    else:
                        print("⚠️ Face size same as original - cropping may not be working")
                else:
                    print("❌ Could not read saved face image")
            else:
                print("❌ No face image was saved")
                
    except Exception as e:
        print(f"❌ Error testing face cropping: {e}")
    
    # Cleanup
    if os.path.exists("test_real.jpg"):
        os.remove("test_real.jpg")

def main():
    """Run all tests"""
    print("Starting Enhanced Face Registration Tests...")
    print("=" * 50)
    
    # Check if API is running
    if not test_api_health():
        print("❌ API is not running. Please start the API first.")
        return
    
    # Test sketch detection
    test_sketch_detection()
    print()
    
    # Test face cropping
    test_face_cropping()
    print()
    
    print("=" * 50)
    print("Tests completed!")

if __name__ == "__main__":
    main()
