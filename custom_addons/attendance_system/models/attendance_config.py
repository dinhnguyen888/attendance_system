from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AttendanceConfig(models.Model):
    _name = 'attendance.config'
    _description = 'Cấu hình điểm danh'
    _rec_name = 'name'
    
    name = fields.Char("Tên cấu hình", required=True, default="Cấu hình điểm danh")
    allowed_wifi_ips = fields.Text("IP WiFi được phép", 
                                   help="Danh sách IP WiFi được phép điểm danh, mỗi IP một dòng")
    wifi_validation_enabled = fields.Boolean("Bật kiểm tra WiFi", default=True,
                                           help="Bật/tắt tính năng kiểm tra WiFi khi điểm danh")

    
    @api.model
    def get_config(self):
        """Lấy cấu hình hiện tại"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({
                'name': 'Cấu hình điểm danh mặc định',
                'allowed_wifi_ips': '',
                'wifi_validation_enabled': True,
            })
        return config
    
    def get_allowed_wifi_ip_list(self):
        """Trả về danh sách IP WiFi được phép"""
        self.ensure_one()
        if not self.allowed_wifi_ips:
            return []
        return [ip.strip() for ip in self.allowed_wifi_ips.split('\n') if ip.strip()]
    
    def is_wifi_ip_allowed(self, wifi_ip):
        """Kiểm tra IP WiFi có được phép không"""
        self.ensure_one()
        if not self.wifi_validation_enabled:
            return True
        
        allowed_list = self.get_allowed_wifi_ip_list()
        if not allowed_list:
            return True  # Nếu không có IP WiFi nào được cấu hình, cho phép tất cả
        
        return wifi_ip in allowed_list
