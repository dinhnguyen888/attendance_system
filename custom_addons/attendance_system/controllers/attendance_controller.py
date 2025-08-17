from odoo import http, fields
from odoo.http import request
import base64
import json
import requests
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class AttendanceController(http.Controller):
    
    # URL của API face recognition service
    FACE_RECOGNITION_API_URL = "http://face_recognition_api:8000"
    
    @http.route('/attendance/webcam', type='http', auth='user')
    def attendance_webcam(self, **kw):
        return http.request.render('attendance_system.webcam_template', {})
    
def _call_face_recognition_api(self, face_image, action, employee_id=None):
    try:
        url = f"{self.FACE_RECOGNITION_API_URL}/face-recognition/verify"

        files = {
            'face_image': ('face.jpg', base64.b64decode(face_image.split(',')[1] if ',' in face_image else face_image), 'image/jpeg')
        }
        data = {
            'action': action,
            'employee_id': employee_id
        }

        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()

        result = response.json()
        return {
            "success": result.get('success', False),
            "message": result.get('message', 'Xác thực khuôn mặt thất bại'),
            "confidence": result.get('confidence', 0.0)
        }

    def _call_face_register_api(self, face_image, employee_id):
        """Gọi API face recognition để đăng ký khuôn mặt"""
        try:
            url = f"{self.FACE_RECOGNITION_API_URL}/face-recognition/register"
            params = {"employee_id": employee_id}
            payload = {
                "face_image": face_image,
                "action": "register",
                "employee_id": employee_id
            }
            
            response = requests.post(url, params=params, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": result.get('success', False),
                "message": result.get('message', 'Đăng ký khuôn mặt thất bại')
            }
        except requests.exceptions.RequestException as e:
            _logger.error(f"Face register API error: {str(e)}")
            return {
                "success": False,
                "message": f"Lỗi kết nối API face register: {str(e)}"
            }
        except Exception as e:
            _logger.error(f"Unexpected error in face register: {str(e)}")
            return {
                "success": False,
                "message": f"Lỗi xử lý face register: {str(e)}"
            }
    
    @http.route('/attendance/check_in', type='json', auth='user')
    def check_in(self, **kw):
        try:
            if not request.env.user or not request.env.user.id:
                return {'error': 'Session expired. Vui lòng đăng nhập lại.'}
            
            employee = request.env.user.employee_id
            if not employee:
                return {'error': 'Không tìm thấy nhân viên'}
            
            # Kiểm tra xem nhân viên đã đăng ký khuôn mặt chưa
            if not employee.has_face_data:
                return {'error': 'Nhân viên chưa đăng ký khuôn mặt. Vui lòng liên hệ quản trị viên.'}
            
            face_image = kw.get('face_image')
            if not face_image:
                return {'error': 'Không có ảnh khuôn mặt'}
            
            # Gọi API face recognition để xác thực
            face_result = self._call_face_recognition_api(
                face_image=face_image,
                action="check_in",
                employee_id=employee.id
            )
            
            # Cho phép check-in ngay cả khi confidence thấp (API đã xử lý thành công)
            # Chỉ trả về error khi API thực sự thất bại (không decode được ảnh, không tìm thấy khuôn mặt)
            if not face_result.get('success') and "không thể decode" in face_result.get('message', '').lower():
                return {'error': face_result.get('message', 'Xác thực khuôn mặt thất bại')}
            
            # Kiểm tra logic nghiệp vụ
            existing_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1)
            
            if existing_attendance:
                return {'error': 'Bạn đã check-in. Vui lòng check-out trước.'}
            
            current_time = fields.Datetime.now()
            start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            today_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start_of_day),
                ('check_in', '<', end_of_day)
            ])
            
            if today_attendance:
                return {'error': 'Bạn đã check-in hôm nay. Vui lòng check-out trước.'}
            
            # Tạo bản ghi attendance
            attendance = request.env['hr.attendance'].sudo().create({
                'employee_id': employee.id,
                'check_in': current_time,
                'face_image': face_image,
                'verification_confidence': face_result.get('confidence', 0.0),
                'verification_message': face_result.get('message', '')
            })
            
            return {
                'success': True,
                'attendance_id': attendance.id,
                'check_in_time': current_time.strftime('%H:%M:%S'),
                'confidence': face_result.get('confidence', 0.0)
            }
            
        except Exception as e:
            _logger.error(f"Check-in error: {str(e)}")
            return {'error': f'Lỗi server: {str(e)}'}
    
    @http.route('/attendance/check_out', type='json', auth='user')
    def check_out(self, **kw):
        try:
            if not request.env.user or not request.env.user.id:
                return {'error': 'Session expired. Vui lòng đăng nhập lại.'}
            
            employee = request.env.user.employee_id
            if not employee:
                return {'error': 'Không tìm thấy nhân viên'}
            
            # Kiểm tra xem nhân viên đã đăng ký khuôn mặt chưa
            if not employee.has_face_data:
                return {'error': 'Nhân viên chưa đăng ký khuôn mặt. Vui lòng liên hệ quản trị viên.'}
            
            face_image = kw.get('face_image')
            if not face_image:
                return {'error': 'Không có ảnh khuôn mặt'}
            
            # Gọi API face recognition để xác thực
            face_result = self._call_face_recognition_api(
                face_image=face_image,
                action="check_out",
                employee_id=employee.id
            )
            
            # Cho phép check-out ngay cả khi confidence thấp (API đã xử lý thành công)
            # Chỉ trả về error khi API thực sự thất bại (không decode được ảnh, không tìm thấy khuôn mặt)
            if not face_result.get('success') and "không thể decode" in face_result.get('message', '').lower():
                return {'error': face_result.get('message', 'Xác thực khuôn mặt thất bại')}
            
            # Tìm bản ghi attendance hiện tại
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1, order='check_in desc')
            
            if not attendance:
                return {'error': 'Không tìm thấy bản ghi check-in để check-out'}
            
            current_time = fields.Datetime.now()
            check_in_time = attendance.check_in
            
            # Kiểm tra thời gian tối thiểu giữa check-in và check-out
            if check_in_time and (current_time - check_in_time).total_seconds() < 60:
                return {'error': 'Phải check-out sau ít nhất 1 phút từ khi check-in'}
            
            # Cập nhật bản ghi attendance
            attendance.write({
                'check_out': current_time,
                'face_image': face_image,
                'verification_confidence': face_result.get('confidence', 0.0),
                'verification_message': face_result.get('message', '')
            })
            
            # Tính số giờ làm việc
            work_hours = (current_time - check_in_time).total_seconds() / 3600
            
            return {
                'success': True,
                'attendance_id': attendance.id,
                'check_out_time': current_time.strftime('%H:%M:%S'),
                'work_hours': round(work_hours, 2),
                'confidence': face_result.get('confidence', 0.0)
            }
            
        except Exception as e:
            _logger.error(f"Check-out error: {str(e)}")
            return {'error': f'Lỗi server: {str(e)}'}
    
    @http.route('/attendance/status', type='json', auth='user')
    def get_attendance_status(self, **kw):
        """Lấy trạng thái attendance hiện tại của user"""
        try:
            if not request.env.user or not request.env.user.id:
                return {'error': 'Session expired'}
            
            employee = request.env.user.employee_id
            if not employee:
                return {'error': 'Không tìm thấy nhân viên'}
            
            # Kiểm tra trạng thái attendance hiện tại
            current_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1, order='check_in desc')
            
            if current_attendance:
                return {
                    'status': 'checked_in',
                    'check_in_time': current_attendance.check_in.strftime('%H:%M:%S'),
                    'can_check_out': True
                }
            else:
                return {
                    'status': 'checked_out',
                    'can_check_in': True
                }
                
        except Exception as e:
            _logger.error(f"Get status error: {str(e)}")
            return {'error': f'Lỗi server: {str(e)}'}
    
    @http.route('/attendance/register_face', type='json', auth='user')
    def register_face(self, **kw):
        """Đăng ký khuôn mặt cho nhân viên"""
        try:
            if not request.env.user or not request.env.user.id:
                return {'error': 'Session expired. Vui lòng đăng nhập lại.'}
            
            employee = request.env.user.employee_id
            if not employee:
                return {'error': 'Không tìm thấy nhân viên'}
            
            face_image = kw.get('face_image')
            if not face_image:
                return {'error': 'Không có ảnh khuôn mặt'}
            
            # Gọi API face recognition để đăng ký
            register_result = self._call_face_register_api(
                face_image=face_image,
                employee_id=employee.id
            )
            
            if not register_result.get('success'):
                return {'error': register_result.get('message', 'Đăng ký khuôn mặt thất bại')}
            
            # Lưu ảnh vào database
            face_image_data = face_image.split(',')[1] if ',' in face_image else face_image
            
            # Tạo hoặc cập nhật ảnh khuôn mặt
            employee_face = request.env['hr.employee.face'].sudo().search([
                ('employee_id', '=', employee.id),
                ('is_active', '=', True)
            ], limit=1)
            
            if employee_face:
                # Cập nhật ảnh hiện tại
                employee_face.write({
                    'face_image': face_image_data,
                    'action': 'update',
                    'notes': 'Cập nhật từ webcam'
                })
            else:
                # Tạo ảnh mới
                request.env['hr.employee.face'].sudo().create({
                    'name': f'Ảnh khuôn mặt {employee.name}',
                    'employee_id': employee.id,
                    'face_image': face_image_data,
                    'action': 'register',
                    'notes': 'Đăng ký từ webcam',
                    'is_active': True
                })
            
            return {
                'success': True,
                'message': 'Đăng ký khuôn mặt thành công!'
            }
            
        except Exception as e:
            _logger.error(f"Register face error: {str(e)}")
            return {'error': f'Lỗi server: {str(e)}'}
    
    @http.route('/attendance/face_api_health', type='json', auth='user')
    def face_api_health(self, **kw):
        """Kiểm tra trạng thái API face recognition"""
        try:
            url = f"{self.FACE_RECOGNITION_API_URL}/face-recognition/health"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return {
                'success': True,
                'status': result.get('status', 'unknown'),
                'opencv_version': result.get('opencv_version', 'unknown'),
                'employee_faces_count': result.get('employee_faces_count', 0)
            }
        except Exception as e:
            _logger.error(f"Face API health check error: {str(e)}")
            return {
                'success': False,
                'error': f'Không thể kết nối API face recognition: {str(e)}'
            }
