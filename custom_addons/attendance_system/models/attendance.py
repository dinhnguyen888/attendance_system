from odoo import models, fields, api
import base64
import logging
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    face_image_data = fields.Binary("Ảnh khuôn mặt đăng ký", attachment=True)
    has_face_data = fields.Boolean("Đã đăng ký khuôn mặt", compute='_compute_has_face_data', store=True)
    face_registration_date = fields.Datetime("Ngày đăng ký khuôn mặt", readonly=True)
    face_management_ids = fields.One2many('hr.employee.face', 'employee_id', string="Quản lý ảnh khuôn mặt")
    
    @api.depends('face_image_data')
    def _compute_has_face_data(self):
        for employee in self:
            employee.has_face_data = bool(employee.face_image_data)
    
    def action_register_face(self):
        """Action để đăng ký khuôn mặt"""
        self.ensure_one()
        return {
            'name': 'Đăng ký khuôn mặt',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.face',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': self.id,
                'default_action': 'register'
            }
        }
    
    def action_manage_faces(self):
        """Action để quản lý ảnh khuôn mặt"""
        self.ensure_one()
        return {
            'name': f'Quản lý ảnh khuôn mặt - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.face',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id}
        }
    
    def action_register_face_with_api(self):
        """Đăng ký ảnh khuôn mặt hiện tại với API"""
        self.ensure_one()
        
        if not self.has_face_data:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': 'Nhân viên chưa có ảnh khuôn mặt để đăng ký',
                    'type': 'danger',
                }
            }
        
        # Tìm ảnh khuôn mặt đang active
        active_face = self.env['hr.employee.face'].search([
            ('employee_id', '=', self.id),
            ('is_active', '=', True)
        ], limit=1)
        
        if not active_face:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': 'Không tìm thấy ảnh khuôn mặt đang sử dụng',
                    'type': 'danger',
                }
            }
        
        # Gọi method đăng ký API từ ảnh khuôn mặt
        return active_face.action_register_with_api()

class HrEmployeeFace(models.Model):
    _name = 'hr.employee.face'
    _description = 'Quản lý ảnh khuôn mặt nhân viên'
    _order = 'create_date desc'
    
    name = fields.Char("Tên ảnh", required=True)
    employee_id = fields.Many2one('hr.employee', string="Nhân viên", required=True, ondelete='cascade')
    face_image = fields.Binary("Ảnh khuôn mặt", attachment=True, required=True)
    face_image_filename = fields.Char("Tên file ảnh")
    is_active = fields.Boolean("Đang sử dụng", default=True)
    action = fields.Selection([
        ('register', 'Đăng ký'),
        ('update', 'Cập nhật'),
        ('backup', 'Sao lưu')
    ], string="Hành động", default='register')
    notes = fields.Text("Ghi chú")
    create_date = fields.Datetime("Ngày tạo", readonly=True)
    write_date = fields.Datetime("Ngày cập nhật", readonly=True)
    
    @api.model
    def create(self, vals):
        """Override create để tự động cập nhật employee và gọi API register"""
        # Kiểm tra xem employee đã có ảnh khuôn mặt active chưa
        if vals.get('employee_id') and vals.get('is_active', True):
            existing_active_face = self.search([
                ('employee_id', '=', vals['employee_id']),
                ('is_active', '=', True)
            ], limit=1)
            
            if existing_active_face:
                from odoo.exceptions import ValidationError
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                raise ValidationError(f"Nhân viên '{employee.name}' đã có ảnh khuôn mặt đang sử dụng. Vui lòng vô hiệu hóa ảnh cũ trước khi đăng ký ảnh mới.")
        
        record = super().create(vals)
        
        if record.is_active and record.employee_id and record.face_image:
            # Cập nhật ảnh chính của employee
            record.employee_id.write({
                'face_image_data': record.face_image,
                'face_registration_date': fields.Datetime.now()
            })
            
            # Gọi API register face
            try:
                import requests
                import base64
                
                if record.face_image:
                    # Odoo binary fields are base64-encoded; decode to raw bytes for multipart
                    face_bytes = base64.b64decode(record.face_image)
                    api_url = "http://face_recognition_api:8000/face-recognition/register"
                    files = {
                        'face_image': ('face.jpg', face_bytes, 'image/jpeg')
                    }
                    data = {
                        'action': 'register',
                        'employee_id': str(record.employee_id.id)
                    }
                    response = requests.post(api_url, files=files, data=data, timeout=30)
                    if response.status_code == 200:
                        _logger.info(f"API register face thành công cho employee {record.employee_id.id}")
                    else:
                        _logger.error(f"API register face thất bại: {response.text}")
                        
            except Exception as e:
                _logger.error(f"Lỗi khi gọi API register face: {str(e)}")
        
        return record
    
    def write(self, vals):
        """Override write để xử lý khi thay đổi trạng thái active và gọi API register"""
        result = super().write(vals)
        if 'is_active' in vals or 'face_image' in vals:
            for record in self:
                if record.is_active and record.employee_id and record.face_image:
                    # Cập nhật ảnh chính của employee
                    record.employee_id.write({
                        'face_image_data': record.face_image,
                        'face_registration_date': fields.Datetime.now()
                    })
                    
                    # Gọi API register face nếu có thay đổi ảnh
                    if 'face_image' in vals:
                        try:
                            import requests
                            import base64
                            
                            face_bytes = base64.b64decode(record.face_image)
                            api_url = "http://face_recognition_api:8000/face-recognition/register"
                            files = {
                                'face_image': ('face.jpg', face_bytes, 'image/jpeg')
                            }
                            data = {
                                'action': 'register',
                                'employee_id': str(record.employee_id.id)
                            }
                            response = requests.post(api_url, files=files, data=data, timeout=30)
                            if response.status_code == 200:
                                _logger.info(f"API register face thành công cho employee {record.employee_id.id}")
                            else:
                                _logger.error(f"API register face thất bại: {response.text}")
                                
                        except Exception as e:
                            _logger.error(f"Lỗi khi gọi API register face: {str(e)}")
        return result
    
    def action_set_as_active(self):
        """Đặt ảnh này làm ảnh chính"""
        self.ensure_one()
        # Tắt tất cả ảnh khác
        self.search([
            ('employee_id', '=', self.employee_id.id),
            ('id', '!=', self.id)
        ]).write({'is_active': False})
        
        # Bật ảnh này
        self.write({'is_active': True})
        
        # Cập nhật employee
        self.employee_id.write({
            'face_image_data': self.face_image,
            'face_registration_date': fields.Datetime.now()
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': f'Đã đặt ảnh "{self.name}" làm ảnh chính cho {self.employee_id.name}',
                'type': 'success',
            }
        }
    
    def action_delete_face(self):
        """Xóa ảnh khuôn mặt - Updated 2025-09-18 18:22"""
        self.ensure_one()
        
        # Gọi API xóa face data trước khi xóa record trong Odoo
        try:
            # Sử dụng controller method có sẵn để gọi API
            from odoo.addons.attendance_system.controllers.attendance_controller import AttendanceController
            controller = AttendanceController()
            api_result = controller._call_face_delete_api(self.employee_id.id)
            
            if not api_result.get('success', False):
                _logger.warning(f"API delete face failed for employee {self.employee_id.id}: {api_result.get('message', 'Unknown error')}")
                # Vẫn tiếp tục xóa record trong Odoo ngay cả khi API thất bại
        except Exception as e:
            _logger.error(f"Error calling face delete API for employee {self.employee_id.id}: {str(e)}")
            # Vẫn tiếp tục xóa record trong Odoo ngay cả khi có lỗi API
        
        # Lưu tên ảnh trước khi xóa
        face_name = self.name
        employee_name = self.employee_id.name
        
        # Nếu đây là ảnh đang active, cần cập nhật lại employee
        if self.is_active:
            # Tìm ảnh khác để đặt làm active (nếu có)
            other_faces = self.search([
                ('employee_id', '=', self.employee_id.id),
                ('id', '!=', self.id),
                ('is_active', '=', False)
            ], limit=1, order='create_date desc')
            
            if other_faces:
                # Đặt ảnh khác làm active
                other_faces.write({'is_active': True})
                self.employee_id.write({
                    'face_image_data': other_faces.face_image,
                    'face_registration_date': fields.Datetime.now()
                })
            else:
                # Không có ảnh khác, xóa ảnh chính của employee
                self.employee_id.write({
                    'face_image_data': False,
                    'face_registration_date': False
                })
        
        # Xóa record khỏi Odoo database
        self.unlink()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': f'Đã xóa ảnh "{face_name}" của nhân viên {employee_name} và dữ liệu face recognition tương ứng',
                'type': 'success',
            }
        }
    
    def action_register_with_api(self):
        """Đăng ký ảnh khuôn mặt với API face recognition"""
        self.ensure_one()
        
        if not self.face_image:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': 'Không có ảnh khuôn mặt để đăng ký',
                    'type': 'danger',
                }
            }
        
        try:
            import requests, base64
            from odoo import fields
            import logging
            _logger = logging.getLogger(__name__)

            # Decode ảnh từ base64 sang bytes
            face_bytes = base64.b64decode(self.face_image)

            api_url = "http://face_recognition_api:8000/face-recognition/register"

            # multipart/form-data
            files = {
                'face_image': ('face.jpg', face_bytes, 'image/jpeg')
            }
            data = {
                'action': 'register',
                'employee_id': str(self.employee_id.id)
            }

            response = requests.post(
                api_url,
                files=files,
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Cập nhật trạng thái
                    self.write({
                        'action': 'register',
                        'notes': f'Đã đăng ký với API thành công - {fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                    })
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Thành công',
                            'message': f'Đã đăng ký ảnh "{self.name}" với API face recognition thành công!',
                            'type': 'success',
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Lỗi API',
                            'message': f'API trả về lỗi: {result.get("message", "Unknown error")}',
                            'type': 'danger',
                        }
                    }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Lỗi kết nối',
                        'message': f'Không thể kết nối API. Status code: {response.status_code}',
                        'type': 'danger',
                    }
                }

        except requests.exceptions.RequestException as e:
            _logger.error(f"API request error: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi kết nối',
                    'message': f'Không thể kết nối đến API face recognition: {str(e)}',
                    'type': 'danger',
                }
            }
        except Exception as e:
            _logger.error(f"Unexpected error in API register: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi hệ thống',
                    'message': f'Lỗi xử lý: {str(e)}',
                    'type': 'danger',
                }
            }

class HrFaceAttendance(models.Model):
    _inherit = 'hr.attendance'
    
    # Ảnh check-in và check-out riêng biệt
    check_in_image = fields.Binary( attachment=True, help="Ảnh khuôn mặt khi check-in")
    check_out_image = fields.Binary(attachment=True, help="Ảnh khuôn mặt khi check-out")
    
    # Thông tin xác thực cho check-in
    check_in_confidence = fields.Float("Độ tin cậy check-in", digits=(3, 2))
    check_in_message = fields.Text("Thông báo xác thực check-in")
    check_in_wifi_ip = fields.Char("IP WiFi check-in", help="IP WiFi khi check-in")
    check_in_wifi_validated = fields.Boolean("WiFi check-in hợp lệ", default=False)
    
    # Thông tin xác thực cho check-out
    check_out_confidence = fields.Float("Độ tin cậy check-out", digits=(3, 2))
    check_out_message = fields.Text("Thông báo xác thực check-out")
    check_out_wifi_ip = fields.Char("IP WiFi check-out", help="IP WiFi khi check-out")
    check_out_wifi_validated = fields.Boolean("WiFi check-out hợp lệ", default=False)
    
    # Giữ lại các trường cũ để tương thích ngược
    face_image = fields.Binary("Ảnh khuôn mặt check-in/out", attachment=True, help="Deprecated: Sử dụng check_in_image và check_out_image")
    verification_confidence = fields.Float("Độ tin cậy xác thực", digits=(3, 2), help="Deprecated: Sử dụng check_in_confidence và check_out_confidence")
    verification_message = fields.Text("Thông báo xác thực", help="Deprecated: Sử dụng check_in_message và check_out_message")
    wifi_ip = fields.Char("IP WiFi", help="Deprecated: Sử dụng check_in_wifi_ip và check_out_wifi_ip")
    wifi_validated = fields.Boolean("WiFi hợp lệ", default=False, help="Deprecated: Sử dụng check_in_wifi_validated và check_out_wifi_validated")

    @api.constrains('employee_id', 'check_in', 'check_out')
    def _check_validity(self):
        """Override constraint để HR có thể bypass validation"""
        # Nếu có context skip_attendance_validation thì bỏ qua validation
        if self.env.context.get('skip_attendance_validation'):
            return
        
        # Gọi constraint gốc cho các user khác
        return super()._check_validity()

    def check_user_permissions(self, action='read'):
        """Kiểm tra quyền của user với bản ghi chấm công"""
        user = self.env.user
        
        # Admin và HR có toàn quyền
        if user.has_group('base.group_system') or user.has_group('attendance_system.group_attendance_hr'):
            return {
                'can_read': True,
                'can_write': True,
                'can_create': True,
                'can_delete': True,
                'message': 'Toàn quyền quản lý chấm công'
            }
        
        # Trưởng phòng: xem và sửa nhân viên trong phòng ban, không được xóa
        if user.has_group('attendance_system.group_attendance_department_manager'):
            if (self.employee_id.department_id and 
                self.employee_id.department_id.manager_id.user_id.id == user.id):
                return {
                    'can_read': True,
                    'can_write': True,
                    'can_create': False,
                    'can_delete': False,
                    'message': 'Quyền xem và sửa chấm công nhân viên trong phòng ban'
                }
            return {
                'can_read': False,
                'can_write': False,
                'can_create': False,
                'can_delete': False,
                'message': 'Chỉ quản lý được nhân viên trong phòng ban mình'
            }
        
        # Nhân viên: chỉ xem và tạo bản ghi của chính mình
        if user.has_group('attendance_system.group_attendance_employee'):
            if self.employee_id.user_id.id == user.id:
                return {
                    'can_read': True,
                    'can_write': True,
                    'can_create': True,
                    'can_delete': False,
                    'message': 'Quyền check-in/check-out và xem lịch sử của mình'
                }
            return {
                'can_read': False,
                'can_write': False,
                'can_create': False,
                'can_delete': False,
                'message': 'Không có quyền xem dữ liệu chấm công của người khác'
            }
        
        return {
            'can_read': False,
            'can_write': False,
            'can_create': False,
            'can_delete': False,
            'message': 'Không có quyền truy cập hệ thống chấm công'
        }


    @api.model
    def create(self, vals):
        user = self.env.user
        
        # Admin và HR có toàn quyền tạo bản ghi chấm công cho bất kỳ ai - bypass validation
        if user.has_group('base.group_system') or user.has_group('attendance_system.group_attendance_hr'):
            # Tạo record với sudo để bypass validation
            record = self.sudo().with_context(skip_attendance_validation=True)
            return super(HrFaceAttendance, record).create(vals)
        
        # Department manager có thể tạo bản ghi chấm công cho nhân viên trong phòng ban
        if user.has_group('attendance_system.group_attendance_department_manager'):
            if 'employee_id' in vals:
                employee_id = vals.get('employee_id')
                employee = self.env['hr.employee'].browse(employee_id)
                # Kiểm tra xem nhân viên có thuộc phòng ban mình quản lý không
                if (employee and employee.department_id and 
                    employee.department_id.manager_id and
                    employee.department_id.manager_id.user_id.id == user.id):
                    return super().create(vals)
                else:
                    raise AccessError("❌ Bạn chỉ có thể tạo bản ghi chấm công cho nhân viên trong phòng ban mình quản lý.")
            return super().create(vals)
        
        # Employee chỉ được tạo bản ghi chấm công cho chính mình
        if user.has_group('attendance_system.group_attendance_employee'):
            # Kiểm tra xem có đang tạo cho chính mình không
            if 'employee_id' in vals:
                employee_id = vals.get('employee_id')
                if user.employee_id and user.employee_id.id == employee_id:
                    return super().create(vals)
                else:
                    raise AccessError("❌ Bạn chỉ có thể tạo bản ghi chấm công cho chính mình.")
            return super().create(vals)
        
        raise AccessError("❌ Bạn không có quyền tạo bản ghi chấm công.")
    
    def action_show_permissions_info(self):
        """Hiển thị thông tin quyền của user với bản ghi này"""
        self.ensure_one()
        permissions = self.check_user_permissions()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thông tin quyền',
                'message': permissions['message'],
                'type': 'info',
                'sticky': True,
            }
        }


    def write(self, vals):
        """Override write để kiểm tra quyền sửa bản ghi chấm công"""
        user = self.env.user
        
        for record in self:
            # Admin và HR: toàn quyền
            if user.has_group('base.group_system') or user.has_group('attendance_system.group_attendance_hr'):
                continue
            
            # Trưởng phòng: sửa bản ghi nhân viên trong phòng ban
            if user.has_group('attendance_system.group_attendance_department_manager'):
                if (record.employee_id.department_id and 
                    record.employee_id.department_id.manager_id.user_id.id == user.id):
                    continue
                raise AccessError("❌ Chỉ được sửa bản ghi nhân viên trong phòng ban mình quản lý")
            
            # Nhân viên: chỉ sửa bản ghi của mình (để check-out)
            if user.has_group('attendance_system.group_attendance_employee'):
                if record.employee_id.user_id.id == user.id:
                    continue
                raise AccessError("❌ Chỉ được sửa bản ghi chấm công của chính mình")
            
            raise AccessError("❌ Không có quyền sửa bản ghi chấm công")
        
        return super().write(vals)

    def unlink(self):
        """Override unlink để kiểm tra quyền xóa - chỉ HR được xóa"""
        user = self.env.user
        
        for record in self:
            # Chỉ Admin và HR được xóa bản ghi chấm công
            if user.has_group('base.group_system') or user.has_group('attendance_system.group_attendance_hr'):
                continue
            
            # Trưởng phòng và nhân viên đều không được xóa
            if user.has_group('attendance_system.group_attendance_department_manager'):
                raise AccessError("❌ Trưởng phòng không được xóa bản ghi chấm công")
            
            if user.has_group('attendance_system.group_attendance_employee'):
                raise AccessError("❌ Nhân viên không được xóa bản ghi chấm công")
            
            raise AccessError("❌ Không có quyền xóa bản ghi chấm công")
        
        return super().unlink()

class ResUsersExtended(models.Model):
    _inherit = 'res.users'
    
    def write(self, vals):
        """Override write để kiểm tra quyền sửa thông tin user"""
        user = self.env.user
        
        for record in self:
            # Admin và HR: toàn quyền
            if user.has_group('base.group_system') or user.has_group('attendance_system.group_attendance_hr'):
                continue
                
            # Trưởng phòng: sửa được user trong phòng ban và chính mình
            if user.has_group('attendance_system.group_attendance_department_manager'):
                if record.id == user.id:
                    continue
                if (record.employee_ids and 
                    record.employee_ids[0].department_id.manager_id.user_id.id == user.id):
                    continue
                raise AccessError("❌ Chỉ sửa được thông tin nhân viên trong phòng ban mình quản lý")
            
            # Nhân viên: chỉ sửa thông tin của chính mình
            if user.has_group('attendance_system.group_attendance_employee'):
                if record.id == user.id:
                    continue
                raise AccessError("❌ Chỉ được sửa thông tin cá nhân của mình")
            
            raise AccessError("❌ Không có quyền sửa thông tin người dùng")
        
        return super().write(vals)

class AttendanceSystemConfig(models.Model):
    _name = 'attendance.system.config'
    _description = 'Cấu hình hệ thống chấm công'
    _rec_name = 'name'
    
    name = fields.Char("Tên cấu hình", required=True)
    api_url = fields.Char("URL API Face Recognition", required=True, default="http://localhost:8000")
    api_key = fields.Char("API Key", help="Khóa xác thực API")
    face_recognition_threshold = fields.Float("Ngưỡng nhận diện khuôn mặt", default=0.6, 
                                            help="Độ chính xác tối thiểu để nhận diện (0.0 - 1.0)")
    max_face_images_per_employee = fields.Integer("Số ảnh khuôn mặt tối đa/nhân viên", default=5)
    backup_enabled = fields.Boolean("Bật sao lưu tự động", default=True)
    backup_frequency = fields.Selection([
        ('daily', 'Hàng ngày'),
        ('weekly', 'Hàng tuần'),
        ('monthly', 'Hàng tháng')
    ], string="Tần suất sao lưu", default='daily')
    backup_retention_days = fields.Integer("Giữ sao lưu (ngày)", default=30)
    system_log_level = fields.Selection([
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error')
    ], string="Mức độ log", default='info')
    
    @api.model
    def get_config(self):
        """Lấy cấu hình hệ thống"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({
                'name': 'Cấu hình mặc định',
                'api_url': 'http://localhost:8000',
                'face_recognition_threshold': 0.6,
                'max_face_images_per_employee': 5,
                'backup_enabled': True,
                'backup_frequency': 'daily',
                'backup_retention_days': 30,
                'system_log_level': 'info'
            })
        return config
    
    def action_test_api_connection(self):
        """Kiểm tra kết nối API"""
        self.ensure_one()
        try:
            import requests
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Thành công',
                        'message': f'Kết nối API thành công: {self.api_url}',
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Lỗi',
                        'message': f'API trả về mã lỗi: {response.status_code}',
                        'type': 'danger',
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi kết nối',
                    'message': f'Không thể kết nối đến API: {str(e)}',
                    'type': 'danger',
                }
            }
    
    def action_backup_system(self):
        """Thực hiện sao lưu hệ thống"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sao lưu',
                'message': 'Đang thực hiện sao lưu hệ thống...',
                'type': 'info',
            }
        }
    
    @api.model
    def create(self, vals):
        """Chỉ admin được tạo cấu hình hệ thống"""
        if not self.env.user.has_group('base.group_system'):
            raise AccessError("❌ Chỉ Admin mới được tạo cấu hình hệ thống")
        return super().create(vals)
    
    def write(self, vals):
        """Chỉ admin được sửa cấu hình hệ thống"""
        if not self.env.user.has_group('base.group_system'):
            raise AccessError("❌ Chỉ Admin mới được sửa cấu hình hệ thống")
        return super().write(vals)
    
    def unlink(self):
        """Chỉ admin được xóa cấu hình hệ thống"""
        if not self.env.user.has_group('base.group_system'):
            raise AccessError("❌ Chỉ Admin mới được xóa cấu hình hệ thống")
        return super().unlink()


