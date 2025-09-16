from odoo import http
from odoo.http import request
import json
import hashlib
import jwt
from datetime import datetime, timedelta
from werkzeug.exceptions import Unauthorized, BadRequest

class MobileApiController(http.Controller):
    
    # JWT Configuration
    JWT_SECRET = "attendance-system-secret-key-2024"
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION = 24 * 60 * 60  # 24 hours
    
    def _create_jwt_token(self, employee_id):
        """Tạo JWT token cho nhân viên"""
        payload = {
            "employee_id": employee_id,
            "exp": datetime.utcnow() + timedelta(seconds=self.JWT_EXPIRATION),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.JWT_SECRET, algorithm=self.JWT_ALGORITHM)
    
    def _verify_jwt_token(self, token):
        """Xác thực JWT token"""
        try:
            payload = jwt.decode(token, self.JWT_SECRET, algorithms=[self.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise Unauthorized("Token đã hết hạn")
        except jwt.InvalidTokenError:
            raise Unauthorized("Token không hợp lệ")
    
    def _get_employee_from_token(self, token):
        """Lấy thông tin nhân viên từ token"""
        try:
            payload = self._verify_jwt_token(token)
            employee_id = payload.get("employee_id")
            if not employee_id:
                raise Unauthorized("Token không hợp lệ")
            
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not employee.exists():
                raise Unauthorized("Không tìm thấy nhân viên")
            
            return employee
        except Exception as e:
            print(f"Error in _get_employee_from_token: {e}")
            raise Unauthorized(f"Token validation failed: {str(e)}")

    def _is_face_registered(self, employee):
        """Kiểm tra nhân viên đã đăng ký khuôn mặt chưa.
        Thứ tự ưu tiên:
        1) Có bản ghi active trong `hr.employee.face`
        2) Có bất kỳ bản ghi `hr.employee.face` nào (kể cả không active)
        3) Fallback: có dữ liệu `employee.face_image_data`
        """
        try:
            active_face = request.env['hr.employee.face'].sudo().search([
                ('employee_id', '=', employee.id),
                ('is_active', '=', True)
            ], limit=1)
            if active_face:
                return True
            any_face = request.env['hr.employee.face'].sudo().search_count([
                ('employee_id', '=', employee.id)
            ])
            if any_face and any_face > 0:
                return True
            # Fallback: trường binary trên employee
            return bool(getattr(employee, 'face_image_data', False))
        except Exception:
            return False
    
    @http.route('/mobile/auth/login', type='http', auth='public', methods=['POST'], csrf=False)
    def mobile_login(self, **kwargs):
        """API đăng nhập cho mobile app"""
        try:
            print(f"DEBUG: mobile_login called with kwargs: {kwargs}")
            
            # Parse request body
            request_data = json.loads(request.httprequest.data.decode('utf-8'))
            print(f"DEBUG: Request data: {request_data}")
            
            username = request_data.get('username') or request_data.get('employee_code') or request_data.get('login')
            password = request_data.get('password')
            
            print(f"DEBUG: Username: {username}, Password: {password}")
            
            if not username or not password:
                return json.dumps({
                    'success': False,
                    'message': 'Vui lòng nhập đầy đủ thông tin'
                })
            
            # Tìm user theo username
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ], limit=1)
            
            if not user:
                return json.dumps({
                    'success': False,
                    'message': 'Tài khoản không tồn tại'
                })
            
            # Kiểm tra mật khẩu bằng Odoo authentication
            try:
                uid = request.env['res.users'].sudo().authenticate(
                    request.db, username, password, {}
                )
                if not uid:
                    return json.dumps({
                        'success': False,
                        'message': 'Mật khẩu không đúng'
                    })
            except Exception as e:
                return json.dumps({
                    'success': False,
                    'message': 'Mật khẩu không đúng'
                })
            
            # Tìm employee tương ứng với user
            employee = request.env['hr.employee'].sudo().search([
                ('user_id', '=', user.id)
            ], limit=1)
            
            if not employee:
                # Fallback: tìm employee theo tên user
                employee = request.env['hr.employee'].sudo().search([
                    ('name', 'ilike', user.name)
                ], limit=1)
                
                if not employee:
                    return json.dumps({
                        'success': False,
                        'message': 'Không tìm thấy thông tin nhân viên'
                    })
            
            # Lấy manager của phòng ban
            department_manager = ''
            if employee.department_id and employee.department_id.manager_id:
                department_manager = employee.department_id.manager_id.name
            elif employee.department_id:
                # Fallback: tìm manager trong cùng phòng ban
                dept_employees = request.env['hr.employee'].sudo().search([
                    ('department_id', '=', employee.department_id.id),
                    ('job_title', 'ilike', 'manager')
                ], limit=1)
                if dept_employees:
                    department_manager = dept_employees.name
            
            token = self._create_jwt_token(employee.id)
            # Xác định ngày bắt đầu làm (ngày tạo tài khoản Odoo)
            start_date = ''
            try:
                if user.create_date:
                    start_date = user.create_date.date().isoformat()
            except Exception:
                start_date = ''
            # Xác định đã đăng ký khuôn mặt
            face_registered = self._is_face_registered(employee)
            
            return json.dumps({
                'success': True,
                'message': 'Đăng nhập thành công',
                'token': token,
                'employee': {
                    'id': employee.id,
                    'name': employee.name,
                    'employee_code': getattr(employee, 'employee_code', '') or '',
                    'department': employee.department_id.name if employee.department_id else '',
                    'position': department_manager or 'Chưa có',
                    'email': employee.work_email or '',
                    'phone': employee.work_phone or '',
                    'face_registered': face_registered,
                    'start_date': start_date
                }
            })
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'Lỗi đăng nhập: {str(e)}'
            })
    
    @http.route('/mobile/employee/profile', type='http', auth='public', methods=['GET'])
    def mobile_profile(self, **kwargs):
        """API lấy thông tin profile nhân viên"""
        try:
            print(f"DEBUG: mobile_profile called with kwargs: {kwargs}")
            
            # Lấy token từ header
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return json.dumps({'error': 'Thiếu token xác thực'}), 401
            
            token = auth_header.split(' ')[1]
            print(f"DEBUG: Token: {token}")
            
            # Xác thực JWT token
            employee = self._get_employee_from_token(token)
            print(f"DEBUG: Employee found: {employee.name}")
            
            last_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id)
            ], order='check_in desc', limit=1)
            
            last_attendance_time = None
            if last_attendance:
                last_attendance_time = last_attendance.check_in.isoformat()
            
            # Lấy manager của phòng ban
            department_manager = ''
            if employee.department_id and employee.department_id.manager_id:
                department_manager = employee.department_id.manager_id.name
            elif employee.department_id:
                # Fallback: tìm manager trong cùng phòng ban
                dept_employees = request.env['hr.employee'].sudo().search([
                    ('department_id', '=', employee.department_id.id),
                    ('job_title', 'ilike', 'manager')
                ], limit=1)
                if dept_employees:
                    department_manager = dept_employees.name
            
            return json.dumps({
                'employee_id': employee.id,
                'name': employee.name,
                'employee_code': getattr(employee, 'employee_code', '') or '',
                'department': employee.department_id.name if employee.department_id else '',
                'position': department_manager or 'Chưa có',
                'email': employee.work_email or '',
                'phone': employee.work_phone or '',
                'face_registered': self._is_face_registered(employee),
                'last_attendance': last_attendance_time,
                'start_date': (employee.user_id.create_date.date().isoformat()
                               if employee.user_id and employee.user_id.create_date else '')
            })
            
        except Unauthorized as e:
            return json.dumps({'error': str(e)})
        except Exception as e:
            return json.dumps({'error': f'Lỗi: {str(e)}'})
    
    @http.route('/mobile/attendance/status', type='http', auth='public', methods=['GET'])
    def mobile_attendance_status(self, **kwargs):
        """API lấy trạng thái chấm công hiện tại"""
        try:
            # Lấy token từ header
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return json.dumps({'error': 'Thiếu token xác thực'}), 401
            
            token = auth_header.split(' ')[1]
            employee = self._get_employee_from_token(token)
            
            today = datetime.now().date()
            today_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', today),
                ('check_in', '<', today + timedelta(days=1))
            ], limit=1)
            
            if not today_attendance:
                status = 'not_started'
                message = 'Chưa chấm công hôm nay'
                check_in = None
                check_out = None
                total_hours = 0.0
            elif today_attendance.check_in and not today_attendance.check_out:
                status = 'working'
                message = 'Đang làm việc'
                check_in = today_attendance.check_in.isoformat()
                check_out = None
                total_hours = 0.0
            else:
                status = 'completed'
                message = 'Đã hoàn thành ngày làm việc'
                check_in = today_attendance.check_in.isoformat()
                check_out = today_attendance.check_out.isoformat()
                total_hours = (today_attendance.check_out - today_attendance.check_in).total_seconds() / 3600
            
            return json.dumps({
                'success': True,
                'status': status,
                'message': message,
                'check_in': check_in,
                'check_out': check_out,
                'total_hours': round(total_hours, 2)
            })
            
        except Unauthorized as e:
            return json.dumps({'error': str(e)})
        except Exception as e:
            return json.dumps({'error': f'Lỗi: {str(e)}'})
    
    @http.route('/mobile/attendance/check', type='http', auth='public', methods=['POST'], csrf=False)
    def mobile_attendance_check(self, **kwargs):
        """API chấm công"""
        try:
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return json.dumps({'error': 'Thiếu token xác thực'})
            
            token = auth_header.split(' ')[1]
            employee = self._get_employee_from_token(token)
            
            request_data = json.loads(request.httprequest.data.decode('utf-8'))
            action = request_data.get('action')
            
            if action not in ['check_in', 'check_out']:
                return json.dumps({
                    'success': False,
                    'message': 'Hành động không hợp lệ'
                })
            
            today = datetime.now().date()
            today_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', today),
                ('check_in', '<', today + timedelta(days=1))
            ], limit=1)
            
            if action == 'check_in':
                if today_attendance:
                    return json.dumps({
                        'success': False,
                        'message': 'Bạn đã check-in hôm nay'
                    })
                
                new_attendance = request.env['hr.attendance'].sudo().create({
                    'employee_id': employee.id,
                    'check_in': datetime.now(),
                })
                
                return json.dumps({
                    'success': True,
                    'message': 'Check-in thành công',
                    'attendance_id': new_attendance.id
                })
                
            elif action == 'check_out':
                if not today_attendance:
                    return json.dumps({
                        'success': False,
                        'message': 'Bạn chưa check-in hôm nay'
                    })
                
                if today_attendance.check_out:
                    return json.dumps({
                        'success': False,
                        'message': 'Bạn đã check-out hôm nay'
                    })
                
                today_attendance.sudo().write({
                    'check_out': datetime.now()
                })
                
                return json.dumps({
                    'success': True,
                    'message': 'Check-out thành công',
                    'attendance_id': today_attendance.id
                })
            
        except Unauthorized as e:
            return json.dumps({'error': str(e)})
        except Exception as e:
            return json.dumps({
                'success': False,
                'message': f'Lỗi chấm công: {str(e)}'
            })
    
    @http.route('/mobile/attendance/history', type='http', auth='public', methods=['GET'])
    def mobile_attendance_history(self, **kwargs):
        """API lấy lịch sử chấm công"""
        try:
            # Lấy token từ header
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return json.dumps({'error': 'Thiếu token xác thực'}), 401
            
            token = auth_header.split(' ')[1]
            employee = self._get_employee_from_token(token)
            
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            domain = [('employee_id', '=', employee.id)]
            
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                    domain.append(('check_in', '>=', start_dt))
                except ValueError:
                    pass
            
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                    domain.append(('check_in', '<', end_dt + timedelta(days=1)))
                except ValueError:
                    pass
            
            attendances = request.env['hr.attendance'].sudo().search(
                domain, order='check_in desc', limit=50
            )
            
            history = []
            for attendance in attendances:
                total_hours = 0.0
                if attendance.check_in and attendance.check_out:
                    total_hours = (attendance.check_out - attendance.check_in).total_seconds() / 3600
                
                history.append({
                    'id': attendance.id,
                    'employee_id': attendance.employee_id.id,
                    'check_in': attendance.check_in.isoformat() if attendance.check_in else None,
                    'check_out': attendance.check_out.isoformat() if attendance.check_out else None,
                    'date': attendance.check_in.date().isoformat() if attendance.check_in else '',
                    'total_hours': round(total_hours, 2) if total_hours > 0 else None,
                    'status': 'completed' if attendance.check_out else 'working'
                })
            
            return json.dumps(history)
            
        except Unauthorized as e:
            return json.dumps({'error': str(e)})
        except Exception as e:
            return json.dumps({'error': f'Lỗi: {str(e)}'})

    @http.route('/mobile/attendance/calendar', type='http', auth='public', methods=['GET'])
    def mobile_attendance_calendar(self, **kwargs):
        """API lấy dữ liệu lịch chấm công"""
        try:
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return json.dumps({'error': 'Thiếu token xác thực'}), 401
            
            token = auth_header.split(' ')[1]
            employee = self._get_employee_from_token(token)
            
            month = int(kwargs.get('month', datetime.now().month))
            year = int(kwargs.get('year', datetime.now().year))
            
            start_date = datetime(year, month, 1).date()
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
            domain = [
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start_date),
                ('check_in', '<=', end_date)
            ]
            
            attendances = request.env['hr.attendance'].sudo().search(
                domain, order='check_in desc'
            )
            
            calendar_data = []
            for attendance in attendances:
                total_hours = 0.0
                if attendance.check_in and attendance.check_out:
                    total_hours = (attendance.check_out - attendance.check_in).total_seconds() / 3600
                
                calendar_data.append({
                    'id': attendance.id,
                    'employee_id': attendance.employee_id.id,
                    'check_in': attendance.check_in.isoformat() if attendance.check_in else None,
                    'check_out': attendance.check_out.isoformat() if attendance.check_out else None,
                    'date': attendance.check_in.date().isoformat() if attendance.check_in else '',
                    'total_hours': round(total_hours, 2) if total_hours > 0 else None,
                    'status': 'completed' if attendance.check_out else 'working'
                })
            
            return json.dumps({
                'success': True,
                'month': month,
                'year': year,
                'attendances': calendar_data
            })
            
        except Unauthorized as e:
            return json.dumps({'error': str(e)})
        except Exception as e:
            return json.dumps({'error': f'Lỗi: {str(e)}'})
