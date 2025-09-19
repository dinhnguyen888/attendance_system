# -*- coding: utf-8 -*-
"""
Unit Tests cho các trường hợp Check-in trong Attendance System
"""

import unittest
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.http import request
from ..controllers.attendance_controller import AttendanceController
from .utils import get_check_in_image


class TestCheckInCases(TransactionCase):
    """Test cases cho chức năng check-in với các trường hợp ảnh khác nhau"""
    
    def setUp(self):
        super().setUp()
        self.controller = AttendanceController()
        
        # Tạo user và employee test
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'test@example.com',
        })
        
        self.test_employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'user_id': self.test_user.id,
        })
        
        # Tạo attendance config
        self.attendance_config = self.env['attendance.config'].create({
            'wifi_validation_enabled': False,
            'allowed_wifi_ips': '',
        })
    
    def _mock_request_env(self):
        """Mock request environment"""
        mock_request = MagicMock()
        mock_request.env.user = self.test_user
        mock_request.env.user.id = self.test_user.id
        mock_request.env.user.employee_id = self.test_employee
        mock_request.env = self.env
        return mock_request
    
    @patch('odoo.http.request')
    def test_check_in_with_dark_image(self, mock_request):
        """Test check-in với ảnh thiếu sáng - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Mock API response cho ảnh thiếu sáng
        with patch.object(self.controller, '_call_face_recognition_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Ảnh quá tối, không thể nhận diện khuôn mặt',
                'confidence': 0.1
            }
            
            result = self.controller.check_in(
                face_image=get_check_in_image('anh-thieu-sang'),
                wifi_ip='192.168.1.100'
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('quá tối', result['error'])
            mock_api.assert_called_once_with(
                face_image=get_check_in_image('anh-thieu-sang'),
                action="check_in",
                employee_id=self.test_employee.id
            )
    
    @patch('odoo.http.request')
    def test_check_in_with_bright_image(self, mock_request):
        """Test check-in với ảnh quá sáng - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Mock API response cho ảnh quá sáng
        with patch.object(self.controller, '_call_face_recognition_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Ảnh quá sáng, bị overexposed',
                'confidence': 0.2
            }
            
            result = self.controller.check_in(
                face_image=get_check_in_image('anh-qua-sang'),
                wifi_ip='192.168.1.100'
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('quá sáng', result['error'])
    
    @patch('odoo.http.request')
    def test_check_in_with_suspicious_object(self, mock_request):
        """Test check-in với ảnh có vật thể khả nghi - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Mock API response cho ảnh có vật thể khả nghi
        with patch.object(self.controller, '_call_face_recognition_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Phát hiện vật thể khả nghi (màn hình điện thoại/TV)',
                'confidence': 0.0
            }
            
            result = self.controller.check_in(
                face_image=get_check_in_image('anh-vat-the-kha-nghi'),
                wifi_ip='192.168.1.100'
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('vật thể khả nghi', result['error'])
    
    @patch('odoo.http.request')
    def test_check_in_with_multiple_faces(self, mock_request):
        """Test check-in với ảnh nhiều khuôn mặt - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Mock API response cho ảnh nhiều khuôn mặt
        with patch.object(self.controller, '_call_face_recognition_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Phát hiện nhiều khuôn mặt trong ảnh. Vui lòng chỉ có 1 người trong khung hình',
                'confidence': 0.0
            }
            
            result = self.controller.check_in(
                face_image=get_check_in_image('anh-nhieu-khuon-mat'),
                wifi_ip='192.168.1.100'
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('nhiều khuôn mặt', result['error'])
    
    @patch('odoo.http.request')
    def test_check_in_with_normal_image_success(self, mock_request):
        """Test check-in với ảnh bình thường - Kỳ vọng: Thành công"""
        mock_request = self._mock_request_env()
        
        # Đăng ký khuôn mặt trước
        self.env['hr.employee.face'].create({
            'name': f'Ảnh khuôn mặt {self.test_employee.name}',
            'employee_id': self.test_employee.id,
            'face_image': get_check_in_image('anh-binh-thuong').split(',')[1],
            'is_active': True
        })
        
        # Mock API response cho ảnh bình thường
        with patch.object(self.controller, '_call_face_recognition_api') as mock_api:
            mock_api.return_value = {
                'success': True,
                'message': 'Xác thực khuôn mặt thành công',
                'confidence': 0.95
            }
            
            result = self.controller.check_in(
                face_image=get_check_in_image('anh-binh-thuong'),
                wifi_ip='192.168.1.100'
            )
            
            # Kiểm tra kết quả
            self.assertIn('success', result)
            self.assertTrue(result['success'])
            self.assertIn('attendance_id', result)
            self.assertIn('check_in_time', result)
            self.assertEqual(result['confidence'], 0.95)
            
            # Kiểm tra attendance record được tạo
            attendance = self.env['hr.attendance'].browse(result['attendance_id'])
            self.assertEqual(attendance.employee_id, self.test_employee)
            self.assertIsNotNone(attendance.check_in)
            self.assertFalse(attendance.check_out)
    
    @patch('odoo.http.request')
    def test_check_in_already_checked_in(self, mock_request):
        """Test check-in khi đã check-in rồi - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Tạo attendance record đã check-in
        existing_attendance = self.env['hr.attendance'].create({
            'employee_id': self.test_employee.id,
            'check_in': '2024-01-01 08:00:00',
        })
        
        with patch.object(self.controller, '_call_face_recognition_api') as mock_api:
            mock_api.return_value = {
                'success': True,
                'message': 'Xác thực khuôn mặt thành công',
                'confidence': 0.95
            }
            
            result = self.controller.check_in(
                face_image=TEST_IMAGES['normal_image'],
                wifi_ip='192.168.1.100'
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('đã check-in', result['error'])
    
    @patch('odoo.http.request')
    def test_check_in_no_face_image(self, mock_request):
        """Test check-in không có ảnh - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        result = self.controller.check_in(wifi_ip='192.168.1.100')
        
        # Kiểm tra kết quả
        self.assertIn('error', result)
        self.assertIn('Không có ảnh khuôn mặt', result['error'])
    
    @patch('odoo.http.request')
    def test_check_in_wifi_validation_failed(self, mock_request):
        """Test check-in với WiFi không hợp lệ - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Bật WiFi validation
        self.attendance_config.write({
            'wifi_validation_enabled': True,
            'allowed_wifi_ips': '192.168.1.1,192.168.1.2'
        })
        
        result = self.controller.check_in(
            face_image=TEST_IMAGES['normal_image'],
            wifi_ip='192.168.1.100'  # IP không được phép
        )
        
        # Kiểm tra kết quả
        self.assertIn('error', result)
        self.assertIn('IP WiFi', result['error'])
        self.assertIn('không được phép', result['error'])
    
    @patch('odoo.http.request')
    def test_check_in_api_connection_error(self, mock_request):
        """Test check-in khi API face recognition lỗi - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Mock API connection error
        with patch.object(self.controller, '_call_face_recognition_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Lỗi kết nối API face recognition: Connection timeout',
                'confidence': 0.0
            }
            
            result = self.controller.check_in(
                face_image=TEST_IMAGES['normal_image'],
                wifi_ip='192.168.1.100'
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('Lỗi kết nối API', result['error'])


class TestCheckInEdgeCases(TransactionCase):
    """Test cases cho các trường hợp biên của check-in"""
    
    def setUp(self):
        super().setUp()
        self.controller = AttendanceController()
    
    @patch('odoo.http.request')
    def test_check_in_no_user_session(self, mock_request):
        """Test check-in khi không có session user"""
        mock_request.env.user = None
        
        result = self.controller.check_in()
        
        self.assertIn('error', result)
        self.assertIn('Session expired', result['error'])
    
    @patch('odoo.http.request')
    def test_check_in_no_employee_record(self, mock_request):
        """Test check-in khi user không có employee record"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.employee_id = None
        mock_request.env.user = mock_user
        
        result = self.controller.check_in()
        
        self.assertIn('error', result)
        self.assertIn('Không tìm thấy nhân viên', result['error'])


if __name__ == '__main__':
    unittest.main()
