# -*- coding: utf-8 -*-
"""
Unit Tests cho các trường hợp Register Face trong Attendance System
"""

import unittest
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.http import request
from ..controllers.attendance_controller import AttendanceController
from .utils import get_register_image


class TestRegisterFaceCases(TransactionCase):
    """Test cases cho chức năng register face với các trường hợp ảnh khác nhau"""
    
    def setUp(self):
        super().setUp()
        self.controller = AttendanceController()
        
        # Tạo user và employee test
        self.test_user = self.env['res.users'].create({
            'name': 'Test User Register',
            'login': 'testuser_register',
            'email': 'test_register@example.com',
        })
        
        self.test_employee = self.env['hr.employee'].create({
            'name': 'Test Employee Register',
            'user_id': self.test_user.id,
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
    def test_register_with_wrong_size_image(self, mock_request):
        """Test register với ảnh sai kích thước - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Mock API response cho ảnh sai kích thước
        with patch.object(self.controller, '_call_face_register_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Ảnh không đúng tỷ lệ. Vui lòng sử dụng ảnh tỷ lệ 3:4 hoặc 4:6 (portrait)',
                'confidence': 0.0
            }
            
            result = self.controller.register_face(
                face_image=get_register_image('anh-sai-kich-thuoc')
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('không đúng tỷ lệ', result['error'])
            mock_api.assert_called_once_with(
                face_image=get_register_image('anh-sai-kich-thuoc'),
                employee_id=self.test_employee.id
            )
    
    @patch('odoo.http.request')
    def test_register_with_wrong_background_color(self, mock_request):
        """Test register với ảnh nền sai màu - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Mock API response cho ảnh nền sai màu
        with patch.object(self.controller, '_call_face_register_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Nền ảnh không phù hợp. Vui lòng sử dụng nền trắng hoặc xanh nhạt',
                'confidence': 0.0
            }
            
            result = self.controller.register_face(
                face_image=get_register_image('anh-nen-sai-mau')
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('Nền ảnh không phù hợp', result['error'])
    
    @patch('odoo.http.request')
    def test_register_with_blurry_image(self, mock_request):
        """Test register với ảnh mờ - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Mock API response cho ảnh mờ
        with patch.object(self.controller, '_call_face_register_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Ảnh không đủ rõ nét. Vui lòng chụp ảnh rõ hơn',
                'confidence': 0.0
            }
            
            result = self.controller.register_face(
                face_image=get_register_image('anh-mo')
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('không đủ rõ nét', result['error'])
    
    @patch('odoo.http.request')
    def test_register_with_normal_image_success(self, mock_request):
        """Test register với ảnh bình thường - Kỳ vọng: Thành công"""
        mock_request = self._mock_request_env()
        
        # Mock API response cho ảnh bình thường
        with patch.object(self.controller, '_call_face_register_api') as mock_api:
            mock_api.return_value = {
                'success': True,
                'message': 'Đăng ký khuôn mặt thành công',
                'confidence': 1.0
            }
            
            result = self.controller.register_face(
                face_image=get_register_image('anh-binh-thuong')
            )
            
            # Kiểm tra kết quả
            self.assertIn('success', result)
            self.assertTrue(result['success'])
            self.assertIn('Đăng ký khuôn mặt thành công', result['message'])
            self.assertEqual(result['confidence'], 1.0)
            self.assertEqual(result['action'], 'đăng ký')
            
            # Kiểm tra face record được tạo
            face_record = self.env['hr.employee.face'].search([
                ('employee_id', '=', self.test_employee.id),
                ('is_active', '=', True)
            ])
            self.assertEqual(len(face_record), 1)
            self.assertEqual(face_record.action, 'register')
    
    @patch('odoo.http.request')
    def test_register_already_has_active_face(self, mock_request):
        """Test register khi đã có ảnh active - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Tạo face record active sẵn
        self.env['hr.employee.face'].create({
            'name': f'Ảnh khuôn mặt {self.test_employee.name}',
            'employee_id': self.test_employee.id,
            'face_image': get_register_image('anh-binh-thuong').split(',')[1],
            'is_active': True
        })
        
        result = self.controller.register_face(
            face_image=get_register_image('anh-binh-thuong')
        )
        
        # Kiểm tra kết quả
        self.assertIn('error', result)
        self.assertIn('đã có ảnh khuôn mặt đang sử dụng', result['error'])
    
    @patch('odoo.http.request')
    def test_register_update_existing_inactive_face(self, mock_request):
        """Test register khi có ảnh inactive cũ - Kỳ vọng: Cập nhật thành công"""
        mock_request = self._mock_request_env()
        
        # Tạo face record inactive
        old_face = self.env['hr.employee.face'].create({
            'name': f'Ảnh khuôn mặt cũ {self.test_employee.name}',
            'employee_id': self.test_employee.id,
            'face_image': get_register_image('anh-binh-thuong').split(',')[1],
            'is_active': False
        })
        
        # Mock API responses
        with patch.object(self.controller, '_call_face_delete_api') as mock_delete_api, \
             patch.object(self.controller, '_call_face_register_api') as mock_register_api:
            
            mock_delete_api.return_value = {
                'success': True,
                'message': 'Xóa dữ liệu khuôn mặt cũ thành công',
                'deleted_files': ['employee_1_face.pkl'],
                'errors': []
            }
            
            mock_register_api.return_value = {
                'success': True,
                'message': 'Đăng ký khuôn mặt thành công',
                'confidence': 1.0
            }
            
            result = self.controller.register_face(
                face_image=get_register_image('anh-binh-thuong')
            )
            
            # Kiểm tra kết quả
            self.assertIn('success', result)
            self.assertTrue(result['success'])
            self.assertIn('Đăng ký khuôn mặt thành công', result['message'])
            
            # Kiểm tra API được gọi
            mock_delete_api.assert_called_once_with(self.test_employee.id)
            mock_register_api.assert_called_once()
            
            # Kiểm tra face record mới được tạo
            active_faces = self.env['hr.employee.face'].search([
                ('employee_id', '=', self.test_employee.id),
                ('is_active', '=', True)
            ])
            self.assertEqual(len(active_faces), 1)
            self.assertEqual(active_faces.action, 'register')
    
    @patch('odoo.http.request')
    def test_register_no_face_image(self, mock_request):
        """Test register không có ảnh - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        result = self.controller.register_face()
        
        # Kiểm tra kết quả
        self.assertIn('error', result)
        self.assertIn('Không có ảnh khuôn mặt', result['error'])
    
    @patch('odoo.http.request')
    def test_register_api_connection_error(self, mock_request):
        """Test register khi API face recognition lỗi - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Mock API connection error
        with patch.object(self.controller, '_call_face_register_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Lỗi kết nối API face register: Connection timeout',
                'confidence': 0.0
            }
            
            result = self.controller.register_face(
                face_image=get_register_image('anh-binh-thuong')
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('Lỗi kết nối API', result['error'])
    
    @patch('odoo.http.request')
    def test_register_invalid_base64_image(self, mock_request):
        """Test register với ảnh base64 không hợp lệ - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        # Mock API response cho ảnh base64 không hợp lệ
        with patch.object(self.controller, '_call_face_register_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Ảnh khuôn mặt không hợp lệ (base64)',
                'confidence': 0.0
            }
            
            result = self.controller.register_face(
                face_image='invalid_base64_string'
            )
            
            # Kiểm tra kết quả
            self.assertIn('error', result)
            self.assertIn('không hợp lệ', result['error'])


class TestRegisterFaceEdgeCases(TransactionCase):
    """Test cases cho các trường hợp biên của register face"""
    
    def setUp(self):
        super().setUp()
        self.controller = AttendanceController()
    
    @patch('odoo.http.request')
    def test_register_no_user_session(self, mock_request):
        """Test register khi không có session user"""
        mock_request.env.user = None
        
        result = self.controller.register_face()
        
        self.assertIn('error', result)
        self.assertIn('Session expired', result['error'])
    
    @patch('odoo.http.request')
    def test_register_no_employee_record(self, mock_request):
        """Test register khi user không có employee record"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.employee_id = None
        mock_request.env.user = mock_user
        
        result = self.controller.register_face()
        
        self.assertIn('error', result)
        self.assertIn('Không tìm thấy nhân viên', result['error'])


class TestRegisterFaceValidationCases(TransactionCase):
    """Test cases chi tiết cho validation ảnh register"""
    
    def setUp(self):
        super().setUp()
        self.controller = AttendanceController()
        
        self.test_user = self.env['res.users'].create({
            'name': 'Test User Validation',
            'login': 'testuser_validation',
            'email': 'test_validation@example.com',
        })
        
        self.test_employee = self.env['hr.employee'].create({
            'name': 'Test Employee Validation',
            'user_id': self.test_user.id,
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
    def test_register_square_image_validation(self, mock_request):
        """Test register với ảnh vuông (1:1) - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        with patch.object(self.controller, '_call_face_register_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Ảnh phải có tỷ lệ 3:4 hoặc 4:6 (portrait), không được là ảnh vuông',
                'confidence': 0.0
            }
            
            result = self.controller.register_face(
                face_image=get_register_image('anh-sai-kich-thuoc')
            )
            
            self.assertIn('error', result)
            self.assertIn('tỷ lệ', result['error'])
    
    @patch('odoo.http.request')
    def test_register_landscape_image_validation(self, mock_request):
        """Test register với ảnh ngang - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        with patch.object(self.controller, '_call_face_register_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Ảnh phải ở định dạng portrait (dọc), không được là landscape (ngang)',
                'confidence': 0.0
            }
            
            # Sử dụng ảnh landscape do bạn cung cấp trong thư mục sai kích thước
            result = self.controller.register_face(
                face_image=get_register_image('anh-sai-kich-thuoc')
            )
            
            self.assertIn('error', result)
            self.assertIn('portrait', result['error'])
    
    @patch('odoo.http.request')
    def test_register_red_background_validation(self, mock_request):
        """Test register với nền đỏ - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        with patch.object(self.controller, '_call_face_register_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Nền ảnh phải là màu trắng hoặc xanh nhạt, không được sử dụng nền đỏ',
                'confidence': 0.0
            }
            
            # Sử dụng ảnh nền sai màu bạn cung cấp trong thư mục tương ứng
            result = self.controller.register_face(
                face_image=get_register_image('anh-nen-sai-mau')
            )
            
            self.assertIn('error', result)
            self.assertIn('nền', result['error'])
    
    @patch('odoo.http.request')
    def test_register_very_blurry_validation(self, mock_request):
        """Test register với ảnh rất mờ - Kỳ vọng: Thất bại"""
        mock_request = self._mock_request_env()
        
        with patch.object(self.controller, '_call_face_register_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'message': 'Ảnh quá mờ, không thể trích xuất đặc trưng khuôn mặt',
                'confidence': 0.0
            }
            
            result = self.controller.register_face(
                face_image=get_register_image('anh-mo')
            )
            
            self.assertIn('error', result)
            self.assertIn('mờ', result['error'])


if __name__ == '__main__':
    unittest.main()
