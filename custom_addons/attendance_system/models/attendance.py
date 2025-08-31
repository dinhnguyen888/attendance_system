from odoo import models, fields, api
import base64
import logging

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
        """Xóa ảnh khuôn mặt"""
        self.ensure_one()
        if self.is_active:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': 'Không thể xóa ảnh đang được sử dụng. Vui lòng chọn ảnh khác làm ảnh chính trước.',
                    'type': 'danger',
                }
            }
        
        self.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': f'Đã xóa ảnh "{self.name}"',
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
    face_image = fields.Binary("Ảnh khuôn mặt check-in/out", attachment=True)
    verification_confidence = fields.Float("Độ tin cậy xác thực", digits=(3, 2))
    verification_message = fields.Text("Thông báo xác thực")
    wifi_name = fields.Char("IP WiFi", help="IP WiFi khi điểm danh")
    wifi_validated = fields.Boolean("WiFi hợp lệ", default=False, help="WiFi có trong danh sách được phép")

class AttendanceSystemConfig(models.Model):
    _name = 'attendance.system.config'
    _description = 'Cấu hình hệ thống chấm công'
    _rec_name = 'name'
    
    name = fields.Char("Tên cấu hình", required=True)
    api_url = fields.Char("URL API Face Recognition", required=True, default="http://localhost:8000")
    api_key = fields.Char("API Key", help="Khóa xác thực API")
    face_recognition_threshold = fields.Float("Ngưỡng nhận diện khuôn mặt", default=0.6, help="Độ chính xác tối thiểu để nhận diện (0.0 - 1.0)")
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
            # Tạo cấu hình mặc định nếu chưa có
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
        # Logic sao lưu hệ thống
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sao lưu',
                'message': 'Đang thực hiện sao lưu hệ thống...',
                'type': 'info',
            }
        }


