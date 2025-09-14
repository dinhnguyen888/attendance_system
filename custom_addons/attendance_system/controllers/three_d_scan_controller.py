from odoo import http, fields
from odoo.http import request
import json
import base64
import os
from datetime import datetime, timedelta
from werkzeug.exceptions import Unauthorized, BadRequest
from werkzeug.utils import secure_filename

class ThreeDScanController(http.Controller):
    
    @http.route('/3d-scan/check-in', type='http', auth='none', methods=['OPTIONS'], csrf=False)
    def check_in_options(self, **kwargs):
        """Handle CORS preflight requests for check-in"""
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
            'Access-Control-Max-Age': '86400'
        }
        return http.Response('', status=200, headers=headers)
    
    @http.route('/3d-scan/check-out', type='http', auth='none', methods=['OPTIONS'], csrf=False)
    def check_out_options(self, **kwargs):
        """Handle CORS preflight requests for check-out"""
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
            'Access-Control-Max-Age': '86400'
        }
        return http.Response('', status=200, headers=headers)
    
    def _return_json_response(self, data, status_code=200):
        """Helper method to return proper JSON response with CORS headers"""
        response = json.dumps(data)
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With'
        }
        return http.Response(response, status=status_code, headers=headers)
    
    @http.route('/3d-scan/check-in', type='http', auth='none', methods=['POST'], csrf=False)
    def check_in(self, **kwargs):
        """API check-in cho 3D scan - chỉ cập nhật database, không gọi API face recognition"""
        try:
            employee_id = request.httprequest.form.get('employee_id')
            image_file = request.httprequest.files.get('check_in_image')
            comparison_image_file = request.httprequest.files.get('comparison_image')  # Ảnh so sánh từ AI
            confidence = float(request.httprequest.form.get('confidence', 0.0))  # Nhận từ face_3D_match_api
            verification_message = request.httprequest.form.get('verification_message', '3D Scan Check-in')
            wifi_ip = request.httprequest.form.get('wifi_ip', 'UNKNOWN_WIFI')  # Nhận từ face_3D_match_api
            
            print(f"[CHECK-IN] Received data: employee_id={employee_id}, confidence={confidence}, wifi_ip={wifi_ip}")
            print(f"[CHECK-IN] Image files: check_in_image={bool(image_file)}, comparison_image={bool(comparison_image_file)}")
            
            if not employee_id:
                return self._return_json_response({
                    'success': False,
                    'message': 'Thiếu thông tin employee_id'
                }, 400)
            
            if not image_file:
                return self._return_json_response({
                    'success': False,
                    'message': 'Thiếu ảnh check-in'
                }, 400)
            
            # Kiểm tra employee tồn tại
            employee = request.env['hr.employee'].with_user(1).browse(int(employee_id))
            if not employee.exists():
                return self._return_json_response({
                    'success': False,
                    'message': 'Không tìm thấy nhân viên'
                }, 400)
            
            # Kiểm tra đã check-in chưa (chưa check-out)
            existing_attendance = request.env['hr.attendance'].with_user(1).search([
                ('employee_id', '=', employee.id),
                ('check_in', '!=', False),
                ('check_out', '=', False)
            ], limit=1)
            
            if existing_attendance:
                return self._return_json_response({
                    'success': False,
                    'message': 'Nhân viên đã check-in, chưa check-out'
                }, 400)
            
            # Kiểm tra logic nghiệp vụ - đã check-in hôm nay chưa
            current_time = fields.Datetime.now()
            start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            today_attendance = request.env['hr.attendance'].with_user(1).search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start_of_day),
                ('check_in', '<', end_of_day)
            ])
            
            if today_attendance:
                return self._return_json_response({
                    'success': False,
                    'message': 'Nhân viên đã check-in hôm nay. Vui lòng check-out trước.'
                }, 400)
            
            # Xử lý ảnh thành base64
            image_data = image_file.read()
            face_image_data = base64.b64encode(image_data).decode('utf-8')
            
            # Xử lý comparison image nếu có
            comparison_image_data = None
            if comparison_image_file:
                comparison_data = comparison_image_file.read()
                comparison_image_data = base64.b64encode(comparison_data).decode('utf-8')
            
            # Tạo bản ghi attendance - dùng superuser để bypass quyền
            attendance_data = {
                'employee_id': employee.id,
                'check_in': current_time,
                'check_in_image': face_image_data,
                'check_in_confidence': confidence,
                'check_in_message': verification_message,
                'check_in_wifi_ip': wifi_ip,
                'check_in_wifi_validated': True
            }
            
            # Không lưu comparison_image vào database - chỉ lưu check_in_image
            
            attendance = request.env['hr.attendance'].with_user(1).create(attendance_data)
            
            return self._return_json_response({
                'success': True,
                'message': 'Check-in thành công',
                'attendance_id': attendance.id,
                'check_in_time': current_time.strftime('%H:%M:%S'),
                'confidence': confidence
            })
            
        except Exception as e:
            return self._return_json_response({
                'success': False,
                'message': f'Lỗi check-in: {str(e)}'
            }, 400)
    
    @http.route('/3d-scan/check-out', type='http', auth='none', methods=['POST'], csrf=False)
    def check_out(self, **kwargs):
        """API check-out cho 3D scan - chỉ cập nhật database, không gọi API face recognition"""
        try:
            employee_id = request.httprequest.form.get('employee_id')
            image_file = request.httprequest.files.get('check_out_image')
            comparison_image_file = request.httprequest.files.get('comparison_image')  # Ảnh so sánh từ AI
            confidence = float(request.httprequest.form.get('confidence', 0.0))  # Nhận từ face_3D_match_api
            verification_message = request.httprequest.form.get('verification_message', '3D Scan Check-out')
            wifi_ip = request.httprequest.form.get('wifi_ip', 'UNKNOWN_WIFI')  # Nhận từ face_3D_match_api
            
            print(f"[CHECK-OUT] Received data: employee_id={employee_id}, confidence={confidence}, wifi_ip={wifi_ip}")
            print(f"[CHECK-OUT] Image files: check_out_image={bool(image_file)}, comparison_image={bool(comparison_image_file)}")
            
            if not employee_id:
                return self._return_json_response({
                    'success': False,
                    'message': 'Thiếu thông tin employee_id'
                }, 400)
            
            if not image_file:
                return self._return_json_response({
                    'success': False,
                    'message': 'Thiếu ảnh check-out'
                }, 400)
            
            # Kiểm tra employee tồn tại
            employee = request.env['hr.employee'].with_user(1).browse(int(employee_id))
            if not employee.exists():
                return self._return_json_response({
                    'success': False,
                    'message': 'Không tìm thấy nhân viên'
                }, 400)
            
            # Kiểm tra đã check-in chưa
            existing_attendance = request.env['hr.attendance'].with_user(1).search([
                ('employee_id', '=', employee.id),
                ('check_in', '!=', False),
                ('check_out', '=', False)
            ], limit=1)
            
            if not existing_attendance:
                return self._return_json_response({
                    'success': False,
                    'message': 'Nhân viên chưa check-in hoặc đã check-out'
                }, 400)
            
            current_time = fields.Datetime.now()
            check_in_time = existing_attendance.check_in
            
            # Kiểm tra thời gian tối thiểu giữa check-in và check-out
            if check_in_time and (current_time - check_in_time).total_seconds() < 60:
                return self._return_json_response({
                    'success': False,
                    'message': 'Phải check-out sau ít nhất 1 phút từ khi check-in'
                }, 400)
            
            # Xử lý ảnh thành base64
            image_data = image_file.read()
            face_image_data = base64.b64encode(image_data).decode('utf-8')
            
            # Xử lý comparison image nếu có
            comparison_image_data = None
            if comparison_image_file:
                comparison_data = comparison_image_file.read()
                comparison_image_data = base64.b64encode(comparison_data).decode('utf-8')
            
            # Cập nhật bản ghi attendance - dùng superuser để bypass quyền
            update_data = {
                'check_out': current_time,
                'check_out_image': face_image_data,
                'check_out_confidence': confidence,
                'check_out_message': verification_message,
                'check_out_wifi_ip': wifi_ip,
                'check_out_wifi_validated': True
            }
            
            # Không lưu comparison_image vào database - chỉ lưu check_out_image
            
            existing_attendance.with_user(1).write(update_data)
            
            # Tính số giờ làm việc
            work_hours = (current_time - check_in_time).total_seconds() / 3600
            
            return self._return_json_response({
                'success': True,
                'message': 'Check-out thành công',
                'attendance_id': existing_attendance.id,
                'check_out_time': current_time.strftime('%H:%M:%S'),
                'work_hours': round(work_hours, 2),
                'confidence': confidence
            })
            
        except Exception as e:
            return self._return_json_response({
                'success': False,
                'message': f'Lỗi check-out: {str(e)}'
            }, 400)
    
    @http.route('/3d-scan/view-3d-scan', type='http', auth='none', methods=['GET'])
    def view_3d_scan(self, **kwargs):
        """API xem dữ liệu 3D scan - chỉ admin mới được phép"""
        try:
            employee_id = kwargs.get('employee_id')
            
            # Kiểm tra quyền admin
            if not request.env.user.has_group('base.group_system'):
                return self._return_json_response({
                    'success': False,
                    'message': 'Chỉ admin mới được phép truy cập'
                }, 403)
            
            if not employee_id:
                return self._return_json_response({
                    'success': False,
                    'message': 'Thiếu thông tin employee_id'
                }, 400)
            
            # Kiểm tra employee tồn tại
            employee = request.env['hr.employee'].with_user(1).browse(int(employee_id))
            if not employee.exists():
                return self._return_json_response({
                    'success': False,
                    'message': 'Không tìm thấy nhân viên'
                }, 400)
            
            # Đường dẫn đến thư mục dữ liệu 3D
            base_path = '/mnt/data_store/WORKSPACE/TEMP_PROJ/attendance_system/face_3D_match_api/employee_data'
            employee_folder = os.path.join(base_path, f'employee_{employee.barcode or employee.id}')
            
            if not os.path.exists(employee_folder):
                return self._return_json_response({
                    'success': False,
                    'message': 'Không tìm thấy dữ liệu 3D của nhân viên'
                }, 404)
            
            # Lấy danh sách file trong thư mục
            files_info = []
            for root, dirs, files in os.walk(employee_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, base_path)
                    file_size = os.path.getsize(file_path)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    
                    files_info.append({
                        'filename': file,
                        'relative_path': relative_path,
                        'size_bytes': file_size,
                        'modified': file_modified,
                        'type': 'file'
                    })
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    relative_path = os.path.relpath(dir_path, base_path)
                    files_info.append({
                        'filename': dir_name,
                        'relative_path': relative_path,
                        'type': 'directory'
                    })
            
            return self._return_json_response({
                'success': True,
                'employee_name': employee.name,
                'employee_code': employee.barcode or str(employee.id),
                'data_path': employee_folder,
                'files': files_info
            })
            
        except Exception as e:
            return self._return_json_response({
                'success': False,
                'message': f'Lỗi: {str(e)}'
            }, 400)
    
    @http.route('/3d-scan/check-employee', type='http', auth='none', methods=['GET'])
    def check_employee(self, **kwargs):
        """API kiểm tra thông tin nhân viên - input: employee_id"""
        try:
            employee_id = kwargs.get('employee_id')
            
            if not employee_id:
                return self._return_json_response({
                    'success': False,
                    'message': 'Thiếu thông tin employee_id'
                }, 400)
            
            # Kiểm tra employee tồn tại
            employee = request.env['hr.employee'].with_user(1).browse(int(employee_id))
            if not employee.exists():
                return self._return_json_response({
                    'success': False,
                    'message': 'Không tìm thấy nhân viên'
                }, 400)
            
            # Lấy thông tin user và role
            user = employee.user_id
            user_roles = []
            if user:
                # Lấy các group của user
                for group in user.groups_id:
                    user_roles.append({
                        'id': group.id,
                        'name': group.name,
                        'category': group.category_id.name if group.category_id else 'Khác'
                    })
            
            return self._return_json_response({
                'success': True,
                'employee_id': employee.id,
                'employee_name': employee.name,
                'employee_code': employee.barcode or str(employee.id),
                'job_title': employee.job_title or '',
                'department': employee.department_id.name if employee.department_id else '',
                'user_id': user.id if user else None,
                'user_login': user.login if user else None,
                'roles': user_roles,
                'is_active': employee.active
            })
            
        except Exception as e:
            return self._return_json_response({
                'success': False,
                'message': f'Lỗi: {str(e)}'
            }, 400)
