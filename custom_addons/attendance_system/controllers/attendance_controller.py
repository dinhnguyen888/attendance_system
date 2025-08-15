from odoo import http, fields
from odoo.http import request
import base64
import json
from datetime import datetime, timedelta

class AttendanceController(http.Controller):
    
    @http.route('/attendance/webcam', type='http', auth='user')
    def attendance_webcam(self, **kw):
        return http.request.render('attendance_system.webcam_template', {})
    
    @http.route('/attendance/check_in', type='json', auth='user')
    def check_in(self, **kw):
        try:
            if not request.env.user or not request.env.user.id:
                return {'error': 'Session expired. Vui lòng đăng nhập lại.'}
            
            employee_id = request.env.user.employee_id.id
            if not employee_id:
                return {'error': 'Không tìm thấy nhân viên'}
            
            face_image = kw.get('face_image')
            if not face_image:
                return {'error': 'Không có ảnh khuôn mặt'}
            
            face_image = face_image.split(',')[1] if ',' in face_image else face_image
            
            existing_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id),
                ('check_out', '=', False)
            ], limit=1)
            
            if existing_attendance:
                return {'error': 'Bạn đã check-in. Vui lòng check-out trước.'}
            
            current_time = fields.Datetime.now()
            start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            today_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', start_of_day),
                ('check_in', '<', end_of_day)
            ])
            
            if today_attendance:
                return {'error': 'Bạn đã check-in hôm nay. Vui lòng check-out trước.'}
            
            attendance = request.env['hr.attendance'].sudo().create({
                'employee_id': employee_id,
                'face_image': face_image,
            })
            
            return {
                'success': True,
                'attendance_id': attendance.id
            }
        except Exception as e:
            return {'error': f'Lỗi server: {str(e)}'}
    
    @http.route('/attendance/check_out', type='json', auth='user')
    def check_out(self, **kw):
        try:
            if not request.env.user or not request.env.user.id:
                return {'error': 'Session expired. Vui lòng đăng nhập lại.'}
            
            employee_id = request.env.user.employee_id.id
            if not employee_id:
                return {'error': 'Không tìm thấy nhân viên'}
            
            face_image = kw.get('face_image')
            if not face_image:
                return {'error': 'Không có ảnh khuôn mặt'}
            
            face_image = face_image.split(',')[1] if ',' in face_image else face_image
            
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id),
                ('check_out', '=', False)
            ], limit=1, order='check_in desc')
            
            if not attendance:
                return {'error': 'Không tìm thấy bản ghi check-in để check-out'}
            
            current_time = fields.Datetime.now()
            check_in_time = attendance.check_in
            
            if check_in_time and (current_time - check_in_time).total_seconds() < 60:
                return {'error': 'Phải check-out sau ít nhất 1 phút từ khi check-in'}
            
            attendance.write({
                'check_out': current_time,
                'face_image': face_image,
            })
            
            return {
                'success': True,
                'attendance_id': attendance.id
            }
        except Exception as e:
            return {'error': f'Lỗi server: {str(e)}'}
