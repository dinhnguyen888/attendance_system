from odoo import http
from odoo.http import request
import json
import base64
import tempfile
import os
from datetime import datetime, timedelta
from werkzeug.exceptions import Unauthorized, BadRequest

class EmbeddedApiController(http.Controller):
    
    # Device token for embedded authentication (can be configured per device)
    DEVICE_TOKENS = {
        'EMBEDDED_001': 'embedded_token_001',
        'EMBEDDED_002': 'embedded_token_002',
        # Add more devices as needed
    }
    
    @http.route('/embedded/auth/login', type='http', auth='public', methods=['POST'], csrf=False)
    def embedded_login(self, **kwargs):
        """API đăng nhập cho embedded device với nhiều phương thức xác thực"""
        try:
            request_data = json.loads(request.httprequest.data.decode('utf-8'))
            employee_code = request_data.get('employee_code')
            password = request_data.get('password')
            pin_code = request_data.get('pin_code')
            device_token = request_data.get('device_token')
            device_id = request_data.get('device_id')
            auth_mode = request_data.get('auth_mode', 'password')  # password, pin, device_token, employee_only
            
            if not employee_code:
                return json.dumps({
                    'success': False,
                    'message': 'Vui lòng nhập mã nhân viên'
                })
            
            # Tìm employee theo code
            employee = request.env['hr.employee'].sudo().search([
                '|', ('barcode', '=', employee_code), ('name', 'ilike', employee_code)
            ], limit=1)
            
            if not employee:
                return json.dumps({
                    'success': False,
                    'message': 'Mã nhân viên không tồn tại'
                })
            
            # Tìm user liên kết với employee
            user = employee.user_id
            if not user:
                # Nếu không có user, tạo session tạm thời cho employee
                user = request.env['res.users'].sudo().search([('login', '=', 'admin')], limit=1)
            
            # Xác thực theo phương thức được chọn
            auth_success = False
            auth_message = ''
            
            if auth_mode == 'password' and password:
                # Xác thực bằng mật khẩu truyền thống
                try:
                    uid = request.env['res.users'].sudo().authenticate(
                        request.db, user.login, password, {}
                    )
                    auth_success = bool(uid)
                    if not auth_success:
                        auth_message = 'Mật khẩu không đúng'
                except Exception:
                    auth_message = 'Mật khẩu không đúng'
                    
            elif auth_mode == 'pin' and pin_code:
                # Xác thực bằng mã PIN (lưu trong employee record)
                if hasattr(employee, 'pin_code') and employee.pin_code == pin_code:
                    auth_success = True
                else:
                    auth_message = 'Mã PIN không đúng'
                    
            elif auth_mode == 'device_token' and device_token and device_id:
                # Xác thực bằng device token
                if device_id in self.DEVICE_TOKENS and self.DEVICE_TOKENS[device_id] == device_token:
                    auth_success = True
                else:
                    auth_message = 'Device token không hợp lệ'
                    
            elif auth_mode == 'employee_only':
                # Chỉ cần mã nhân viên (ít bảo mật - chỉ dùng trong môi trường tin cậy)
                auth_success = True
                
            else:
                auth_message = 'Phương thức xác thực không hợp lệ hoặc thiếu thông tin'
            
            if not auth_success:
                return json.dumps({
                    'success': False,
                    'message': auth_message or 'Xác thực thất bại'
                })
            
            # Xác thực thành công
            return json.dumps({
                'success': True,
                'message': 'Đăng nhập thành công',
                'employee_id': employee.id,
                'employee_name': employee.name,
                'employee_code': employee.barcode or employee_code,
                'auth_mode': auth_mode
            })
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'Lỗi hệ thống: {str(e)}'
            })
    
    @http.route('/embedded/auth/pin_setup', type='http', auth='public', methods=['POST'], csrf=False)
    def setup_pin_code(self, **kwargs):
        """API thiết lập mã PIN cho nhân viên"""
        try:
            request_data = json.loads(request.httprequest.data.decode('utf-8'))
            employee_code = request_data.get('employee_code')
            password = request_data.get('password')
            new_pin = request_data.get('new_pin')
            
            if not employee_code or not password or not new_pin:
                return json.dumps({
                    'success': False,
                    'message': 'Thiếu thông tin bắt buộc'
                })
            
            if len(new_pin) < 4 or len(new_pin) > 8:
                return json.dumps({
                    'success': False,
                    'message': 'Mã PIN phải có từ 4-8 ký tự'
                })
            
            # Tìm employee
            employee = request.env['hr.employee'].sudo().search([
                '|', ('barcode', '=', employee_code), ('name', 'ilike', employee_code)
            ], limit=1)
            
            if not employee:
                return json.dumps({
                    'success': False,
                    'message': 'Mã nhân viên không tồn tại'
                })
            
            # Xác thực mật khẩu hiện tại
            user = employee.user_id
            if user:
                try:
                    uid = request.env['res.users'].sudo().authenticate(
                        request.db, user.login, password, {}
                    )
                    if not uid:
                        return json.dumps({
                            'success': False,
                            'message': 'Mật khẩu không đúng'
                        })
                except Exception:
                    return json.dumps({
                        'success': False,
                        'message': 'Mật khẩu không đúng'
                    })
            
            # Lưu PIN code (cần thêm field pin_code vào hr.employee model)
            try:
                employee.sudo().write({'pin_code': new_pin})
                return json.dumps({
                    'success': True,
                    'message': 'Thiết lập mã PIN thành công'
                })
            except Exception as e:
                return json.dumps({
                    'success': False,
                    'message': f'Không thể lưu mã PIN: {str(e)}'
                })
                
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'Lỗi hệ thống: {str(e)}'
            })
    
    @http.route('/embedded/attendance/check-in', type='http', auth='public', methods=['POST'], csrf=False)
    def embedded_check_in(self, **kwargs):
        """API check-in cho embedded device - sử dụng endpoint có sẵn"""
        try:
            employee_id = request.httprequest.form.get('employee_id')
            image_file = request.httprequest.files.get('image')
            wifi_ip = request.httprequest.form.get('wifi_ip', '192.168.1.100')  # Default embedded IP
            
            if not employee_id:
                return json.dumps({
                    'success': False,
                    'message': 'Thiếu thông tin nhân viên'
                })
            
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if not employee.exists():
                return json.dumps({
                    'success': False,
                    'message': 'Không tìm thấy nhân viên'
                })
            
            # Xử lý ảnh thành base64
            face_image = None
            if image_file:
                image_data = image_file.read()
                face_image = 'data:image/jpeg;base64,' + base64.b64encode(image_data).decode('utf-8')
            
            if not face_image:
                return json.dumps({
                    'success': False,
                    'message': 'Thiếu ảnh khuôn mặt'
                })
            
            # Tạo fake user context cho employee
            user = employee.user_id
            if not user:
                return json.dumps({
                    'success': False,
                    'message': 'Nhân viên chưa có tài khoản user'
                })
            
            # Gọi controller check_in có sẵn với context của user
            from . import attendance_controller as att_ctrl
            attendance_controller = att_ctrl.AttendanceController()
            
            # Tạm thời set user context
            original_user = request.env.user
            request.env = request.env(user=user)
            
            try:
                result = attendance_controller.check_in(
                    face_image=face_image,
                    wifi_ip=wifi_ip
                )
                
                if result.get('success'):
                    return json.dumps({
                        'success': True,
                        'message': 'Check-in thành công',
                        'attendance_id': result.get('attendance_id'),
                        'check_in_time': result.get('check_in_time'),
                        'confidence': result.get('confidence', 0.0)
                    })
                else:
                    return json.dumps({
                        'success': False,
                        'message': result.get('error', 'Check-in thất bại')
                    })
                    
            finally:
                # Restore original user context
                request.env = request.env(user=original_user)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'Lỗi check-in: {str(e)}'
            })
    
    @http.route('/embedded/attendance/check-out', type='http', auth='public', methods=['POST'], csrf=False)
    def embedded_check_out(self, **kwargs):
        """API check-out cho embedded device - sử dụng endpoint có sẵn"""
        try:
            employee_id = request.httprequest.form.get('employee_id')
            image_file = request.httprequest.files.get('image')
            wifi_ip = request.httprequest.form.get('wifi_ip', '192.168.1.100')  # Default embedded IP
            
            if not employee_id:
                return json.dumps({
                    'success': False,
                    'message': 'Thiếu thông tin nhân viên'
                })
            
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if not employee.exists():
                return json.dumps({
                    'success': False,
                    'message': 'Không tìm thấy nhân viên'
                })
            
            # Xử lý ảnh thành base64
            face_image = None
            if image_file:
                image_data = image_file.read()
                face_image = 'data:image/jpeg;base64,' + base64.b64encode(image_data).decode('utf-8')
            
            if not face_image:
                return json.dumps({
                    'success': False,
                    'message': 'Thiếu ảnh khuôn mặt'
                })
            
            # Tạo fake user context cho employee
            user = employee.user_id
            if not user:
                return json.dumps({
                    'success': False,
                    'message': 'Nhân viên chưa có tài khoản user'
                })
            
            # Gọi controller check_out có sẵn với context của user
            from . import attendance_controller as att_ctrl
            attendance_controller = att_ctrl.AttendanceController()
            
            # Tạm thời set user context
            original_user = request.env.user
            request.env = request.env(user=user)
            
            try:
                result = attendance_controller.check_out(
                    face_image=face_image,
                    wifi_ip=wifi_ip
                )
                
                if result.get('success'):
                    return json.dumps({
                        'success': True,
                        'message': 'Check-out thành công',
                        'attendance_id': result.get('attendance_id'),
                        'check_out_time': result.get('check_out_time'),
                        'work_hours': result.get('work_hours', 0.0),
                        'confidence': result.get('confidence', 0.0)
                    })
                else:
                    return json.dumps({
                        'success': False,
                        'message': result.get('error', 'Check-out thất bại')
                    })
                    
            finally:
                # Restore original user context
                request.env = request.env(user=original_user)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'Lỗi check-out: {str(e)}'
            })
    
    @http.route('/embedded/attendance/history', type='http', auth='public', methods=['GET'])
    def embedded_attendance_history(self, **kwargs):
        """API lấy lịch sử chấm công cho embedded device"""
        try:
            employee_id = kwargs.get('employee_id')
            if not employee_id:
                return json.dumps({
                    'success': False,
                    'message': 'Thiếu thông tin nhân viên'
                })
            
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if not employee.exists():
                return json.dumps({
                    'success': False,
                    'message': 'Không tìm thấy nhân viên'
                })
            
            # Lấy lịch sử 30 ngày gần nhất
            start_date = datetime.now().date() - timedelta(days=30)
            attendances = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start_date)
            ], order='check_in desc', limit=50)
            
            history = []
            for attendance in attendances:
                total_hours = 0.0
                if attendance.check_in and attendance.check_out:
                    total_hours = (attendance.check_out - attendance.check_in).total_seconds() / 3600
                
                history.append({
                    'id': attendance.id,
                    'date': attendance.check_in.date().isoformat(),
                    'check_in': attendance.check_in.strftime('%H:%M:%S') if attendance.check_in else None,
                    'check_out': attendance.check_out.strftime('%H:%M:%S') if attendance.check_out else None,
                    'total_hours': round(total_hours, 2) if total_hours > 0 else None,
                    'status': 'completed' if attendance.check_out else 'working'
                })
            
            return json.dumps({
                'success': True,
                'employee_name': employee.name,
                'history': history
            })
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'Lỗi: {str(e)}'
            })
