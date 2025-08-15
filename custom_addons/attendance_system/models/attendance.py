from odoo import models, fields, api

class HrFaceAttendance(models.Model):
    _inherit = 'hr.attendance'
    face_image = fields.Binary("Ảnh khuôn mặt")
