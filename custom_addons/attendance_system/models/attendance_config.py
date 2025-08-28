from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AttendanceConfig(models.Model):
    _name = 'attendance.config'
    _description = 'Cấu hình điểm danh'
    _rec_name = 'name'
    
    name = fields.Char("Tên cấu hình", required=True, default="Cấu hình điểm danh")
    allowed_wifi_names = fields.Text("Tên WiFi được phép", 
                                   help="Danh sách tên WiFi được phép điểm danh, mỗi tên một dòng")
    wifi_validation_enabled = fields.Boolean("Bật kiểm tra WiFi", default=True,
                                           help="Bật/tắt tính năng kiểm tra WiFi khi điểm danh")
    show_checkin_images = fields.Boolean("Hiển thị ảnh check-in/out", default=True,
                                       help="Hiển thị ảnh check-in/out trong trang overview")
    
    @api.model
    def get_config(self):
        """Lấy cấu hình hiện tại"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({
                'name': 'Cấu hình điểm danh mặc định',
                'allowed_wifi_names': '',
                'wifi_validation_enabled': True,
                'show_checkin_images': True
            })
        return config
    
    def get_allowed_wifi_list(self):
        """Trả về danh sách WiFi được phép"""
        self.ensure_one()
        if not self.allowed_wifi_names:
            return []
        return [name.strip() for name in self.allowed_wifi_names.split('\n') if name.strip()]
    
    def is_wifi_allowed(self, wifi_name):
        """Kiểm tra WiFi có được phép không"""
        self.ensure_one()
        if not self.wifi_validation_enabled:
            return True
        
        allowed_list = self.get_allowed_wifi_list()
        if not allowed_list:
            return True  # Nếu không có WiFi nào được cấu hình, cho phép tất cả
        
        return wifi_name in allowed_list
