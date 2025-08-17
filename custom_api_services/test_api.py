#!/usr/bin/env python3
"""
Test script cho Face Recognition API
"""

import requests
import base64
import json
import time

# Cấu hình
API_BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_face.jpg"  # Tạo file ảnh test hoặc thay đổi path

def encode_image_to_base64(image_path):
    """Encode ảnh thành base64"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Không tìm thấy file ảnh: {image_path}")
        return None

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/face-recognition/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_face_verification(face_image, action="check_in", employee_id=1):
    """Test face verification endpoint"""
    print(f"🔍 Testing face verification for {action}...")
    
    payload = {
        "face_image": face_image,
        "action": action,
        "employee_id": employee_id
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/face-recognition/verify",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Face verification {action} result: {data}")
            return data.get('success', False)
        else:
            print(f"❌ Face verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Face verification error: {e}")
        return False

def test_face_registration(face_image, employee_id=1):
    """Test face registration endpoint"""
    print(f"🔍 Testing face registration for employee {employee_id}...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/face-recognition/register",
            params={"employee_id": employee_id},
            json={"face_image": face_image, "action": "register", "employee_id": employee_id},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Face registration result: {data}")
            return data.get('success', False)
        else:
            print(f"❌ Face registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Face registration error: {e}")
        return False

def create_test_image():
    """Tạo ảnh test đơn giản (nếu không có ảnh thật)"""
    try:
        import numpy as np
        import cv2
        
        # Tạo ảnh test đơn giản
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        img.fill(128)  # Màu xám
        
        # Vẽ hình tròn đơn giản để giả lập khuôn mặt
        cv2.circle(img, (150, 150), 80, (255, 255, 255), -1)
        cv2.circle(img, (130, 130), 10, (0, 0, 0), -1)  # Mắt trái
        cv2.circle(img, (170, 130), 10, (0, 0, 0), -1)  # Mắt phải
        cv2.circle(img, (150, 170), 15, (0, 0, 0), -1)  # Miệng
        
        cv2.imwrite("test_face.jpg", img)
        print("✅ Created test image: test_face.jpg")
        return True
    except ImportError:
        print("❌ OpenCV not available for creating test image")
        return False
    except Exception as e:
        print(f"❌ Error creating test image: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Face Recognition API Tests")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health_check():
        print("❌ API không khả dụng. Dừng test.")
        return
    
    # Test 2: Tạo hoặc load ảnh test
    face_image = encode_image_to_base64(TEST_IMAGE_PATH)
    if not face_image:
        print("📸 Creating test image...")
        if create_test_image():
            face_image = encode_image_to_base64(TEST_IMAGE_PATH)
        else:
            print("❌ Không thể tạo ảnh test. Dừng test.")
            return
    
    if not face_image:
        print("❌ Không thể encode ảnh. Dừng test.")
        return
    
    print(f"✅ Loaded test image: {len(face_image)} characters")
    
    # Test 3: Face registration
    print("\n" + "=" * 50)
    registration_success = test_face_registration(face_image, employee_id=1)
    
    # Test 4: Face verification for check-in
    print("\n" + "=" * 50)
    checkin_success = test_face_verification(face_image, "check_in", employee_id=1)
    
    # Test 5: Face verification for check-out
    print("\n" + "=" * 50)
    checkout_success = test_face_verification(face_image, "check_out", employee_id=1)
    
    # Test 6: Test với employee_id khác
    print("\n" + "=" * 50)
    test_face_verification(face_image, "check_in", employee_id=2)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"Health Check: {'✅ PASS' if True else '❌ FAIL'}")
    print(f"Registration: {'✅ PASS' if registration_success else '❌ FAIL'}")
    print(f"Check-in: {'✅ PASS' if checkin_success else '❌ FAIL'}")
    print(f"Check-out: {'✅ PASS' if checkout_success else '❌ FAIL'}")
    
    if all([registration_success, checkin_success, checkout_success]):
        print("\n🎉 All tests passed! API is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
