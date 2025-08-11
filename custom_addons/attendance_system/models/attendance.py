from odoo import models, fields, api

class HrFaceAttendance(models.Model):
    _inherit = 'hr.attendance'  # kế thừa model chấm công sẵn có

    face_image = fields.Binary("Ảnh khuôn mặt")
