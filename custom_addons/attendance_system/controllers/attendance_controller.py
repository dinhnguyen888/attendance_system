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
    
    def _call_face_recognition_api(self, face_image, action, employee_id):
        """Gọi API face recognition để xác thực khuôn mặt. Trả về dict chuẩn hóa."""
        try:
            url = f"{self.FACE_RECOGNITION_API_URL}/face-recognition/verify"

            if not face_image:
                return {"success": False, "message": "Thiếu ảnh khuôn mặt", "confidence": 0.0}

            if not employee_id:
                return {"success": False, "message": "Thiếu employee_id", "confidence": 0.0}

            # Chuyển base64 thành file bytes
            face_image_data = face_image.split(',')[1] if ',' in face_image else face_image
            try:
                face_bytes = base64.b64decode(face_image_data)
            except Exception:
                return {"success": False, "message": "Ảnh khuôn mặt không hợp lệ (base64)", "confidence": 0.0}

            files = {'face_image': ('face.jpg', face_bytes, 'image/jpeg')}
            data = {'action': action, 'employee_id': str(employee_id)}

            response = requests.post(url, files=files, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Chuẩn hóa trường trả về để FE luôn nhận đúng kiểu
            success = bool(result.get('success', False))
            message = str(result.get('message', ''))
            confidence = float(result.get('confidence', 0.0) or 0.0)

            return {"success": success, "message": message, "confidence": confidence}
        except requests.exceptions.RequestException as e:
            _logger.error(f"Face recognition API error: {str(e)}")
            return {"success": False, "message": f"Lỗi kết nối API face recognition: {str(e)}", "confidence": 0.0}
        except Exception as e:
            _logger.error(f"Unexpected error in face recognition: {str(e)}")
            return {"success": False, "message": f"Lỗi xử lý face recognition: {str(e)}", "confidence": 0.0}

    def _call_face_delete_api(self, employee_id):
        """Gọi API face recognition để xóa dữ liệu khuôn mặt. Trả về dict chuẩn hóa."""
        try:
            url = f"{self.FACE_RECOGNITION_API_URL}/face-recognition/employee/{employee_id}"

            if not employee_id:
                return {"success": False, "message": "Thiếu employee_id"}

            response = requests.delete(url, timeout=30)
            response.raise_for_status()
            result = response.json()

            success = bool(result.get('success', False))
            message = str(result.get('message', ''))
            deleted_files = result.get('deleted_files', [])
            errors = result.get('errors', [])
            
            return {
                "success": success, 
                "message": message, 
                "deleted_files": deleted_files,
                "errors": errors
            }
        except requests.exceptions.RequestException as e:
            _logger.error(f"Face delete API error: {str(e)}")
            return {"success": False, "message": f"Lỗi kết nối API face delete: {str(e)}"}
        except Exception as e:
            _logger.error(f"Unexpected error in face delete: {str(e)}")
            return {"success": False, "message": f"Lỗi xử lý face delete: {str(e)}"}

    def _call_face_register_api(self, face_image, employee_id):
        """Gọi API face recognition để đăng ký khuôn mặt. Trả về dict chuẩn hóa."""
        try:
            url = f"{self.FACE_RECOGNITION_API_URL}/face-recognition/register"

            if not face_image:
                return {"success": False, "message": "Thiếu ảnh khuôn mặt"}

            if not employee_id:
                return {"success": False, "message": "Thiếu employee_id"}

            # Đăng ký dùng multipart/form-data giống verify để đồng nhất
            face_image_data = face_image.split(',')[1] if ',' in face_image else face_image
            try:
                face_bytes = base64.b64decode(face_image_data)
            except Exception:
                return {"success": False, "message": "Ảnh khuôn mặt không hợp lệ (base64)"}

            files = {'face_image': ('face.jpg', face_bytes, 'image/jpeg')}
            data = {'action': 'register', 'employee_id': str(employee_id)}

            response = requests.post(url, files=files, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            success = bool(result.get('success', False))
            message = str(result.get('message', ''))
            confidence = float(result.get('confidence', 0.0) or 0.0)
            
            return {"success": success, "message": message, "confidence": confidence}
        except requests.exceptions.RequestException as e:
            _logger.error(f"Face register API error: {str(e)}")
            return {"success": False, "message": f"Lỗi kết nối API face register: {str(e)}"}
        except Exception as e:
            _logger.error(f"Unexpected error in face register: {str(e)}")
            return {"success": False, "message": f"Lỗi xử lý face register: {str(e)}"}
    
    @http.route('/attendance/check_in', type='json', auth='user')
    def check_in(self, **kw):
        try:
            if not request.env.user or not request.env.user.id:
                return {'error': 'Session expired. Vui lòng đăng nhập lại.'}
            
            employee = request.env.user.employee_id
            if not employee:
                return {'error': 'Không tìm thấy nhân viên'}
            
            face_image = kw.get('face_image')
            if not face_image:
                return {'error': 'Không có ảnh khuôn mặt'}
            
            # Gọi API face recognition để xác thực
            face_result = self._call_face_recognition_api(
                face_image=face_image,
                action="check_in",
                employee_id=employee.id
            )
            
            # Nếu API thất bại, trả về ngay để UI hiển thị đúng
            if not face_result.get('success'):
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
            
            face_image = kw.get('face_image')
            if not face_image:
                return {'error': 'Không có ảnh khuôn mặt'}
            
            # Gọi API face recognition để xác thực
            face_result = self._call_face_recognition_api(
                face_image=face_image,
                action="check_out",
                employee_id=employee.id
            )
            
            # Nếu API thất bại, trả về ngay để UI hiển thị đúng
            if not face_result.get('success'):
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
                'confidence': float(face_result.get('confidence', 0.0) or 0.0)
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
            
            # Kiểm tra xem nhân viên đã đăng ký khuôn mặt chưa (chỉ cho phép 1 ảnh active)
            has_face_data = request.env['hr.employee.face'].sudo().search([
                ('employee_id', '=', employee.id),
                ('is_active', '=', True)
            ], limit=1)
            
            # Đảm bảo chỉ có 1 ảnh active cho mỗi nhân viên
            face_count = request.env['hr.employee.face'].sudo().search_count([
                ('employee_id', '=', employee.id),
                ('is_active', '=', True)
            ])
            
            if face_count > 1:
                _logger.warning(f"Employee {employee.id} has {face_count} active face records. Fixing...")
                # Giữ lại bản ghi mới nhất, vô hiệu hóa các bản ghi cũ
                all_faces = request.env['hr.employee.face'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('is_active', '=', True)
                ], order='create_date desc')
                
                if len(all_faces) > 1:
                    old_faces = all_faces[1:]  # Tất cả trừ bản ghi mới nhất
                    old_faces.write({'is_active': False, 'notes': 'Vô hiệu hóa do trùng lặp'})
                    has_face_data = all_faces[0]  # Giữ lại bản ghi mới nhất
            
            if not has_face_data:
                return {
                    'status': 'no_face_registered',
                    'message': 'Nhân viên chưa đăng ký khuôn mặt',
                    'can_check_in': False,
                    'can_check_out': False,
                    'need_register': True
                }
            
            # Kiểm tra trạng thái attendance hiện tại
            current_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1, order='check_in desc')
            
            if current_attendance:
                return {
                    'status': 'checked_in',
                    'check_in_time': current_attendance.check_in.strftime('%H:%M:%S'),
                    'can_check_in': False,
                    'can_check_out': True,
                    'need_register': False
                }
            else:
                return {
                    'status': 'checked_out',
                    'can_check_in': True,
                    'can_check_out': False,
                    'need_register': False
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
            
            # Kiểm tra xem nhân viên đã có ảnh khuôn mặt chưa
            existing_face = request.env['hr.employee.face'].sudo().search([
                ('employee_id', '=', employee.id),
                ('is_active', '=', True)
            ], limit=1)
            
            # Nếu đã có ảnh, xóa dữ liệu cũ trên API server trước
            if existing_face:
                _logger.info(f"Deleting existing face data for employee {employee.id} before registering new image")
                delete_result = self._call_face_delete_api(employee.id)
                
                if not delete_result.get('success'):
                    _logger.warning(f"Failed to delete existing face data: {delete_result.get('message')}")
                    # Tiếp tục đăng ký mới dù xóa thất bại
                else:
                    _logger.info(f"Successfully deleted files: {delete_result.get('deleted_files', [])}")
                
                # Vô hiệu hóa bản ghi cũ trong Odoo
                existing_face.write({
                    'is_active': False,
                    'notes': f"Vô hiệu hóa do cập nhật ảnh mới - {fields.Datetime.now()}"
                })
            
            # Gọi API face recognition để đăng ký ảnh mới
            register_result = self._call_face_register_api(
                face_image=face_image,
                employee_id=employee.id
            )
            
            if not register_result.get('success'):
                return {'error': register_result.get('message', 'Đăng ký khuôn mặt thất bại')}
            
            # Lưu ảnh mới vào database
            face_image_data = face_image.split(',')[1] if ',' in face_image else face_image
            
            # Luôn tạo bản ghi mới để đảm bảo chỉ có 1 ảnh active
            request.env['hr.employee.face'].sudo().create({
                'name': f'Ảnh khuôn mặt {employee.name}',
                'employee_id': employee.id,
                'face_image': face_image_data,
                'action': 'update' if existing_face else 'register',
                'notes': f"{'Cập nhật' if existing_face else 'Đăng ký'} từ webcam - {fields.Datetime.now()}",
                'is_active': True
            })
            
            action_text = 'Cập nhật' if existing_face else 'Đăng ký'
            
            return {
                'success': True,
                'message': f'{action_text} khuôn mặt thành công!',
                'confidence': register_result.get('confidence', 1.0),
                'action': action_text.lower()
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
                'employee_faces_count': result.get('employee_faces_count', 0),
                'insightface': result.get('insightface', False),
                'cosine_threshold': result.get('cosine_threshold', 0.5),
                'embedding_files': result.get('embedding_files', 0),
                'embedding_samples': result.get('embedding_samples', 0)
            }
        except Exception as e:
            _logger.error(f"Face API health check error: {str(e)}")
            return {
                'success': False,
                'error': f'Không thể kết nối API face recognition: {str(e)}'
            }