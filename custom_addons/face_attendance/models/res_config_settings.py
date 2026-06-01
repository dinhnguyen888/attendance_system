from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    face_ai_grpc_target = fields.Char(related="company_id.face_ai_grpc_target", readonly=False)
    face_default_threshold = fields.Float(related="company_id.face_default_threshold", readonly=False)
    face_min_valid_frames = fields.Integer(related="company_id.face_min_valid_frames", readonly=False)
    face_max_spoofing_error_rate = fields.Float(related="company_id.face_max_spoofing_error_rate", readonly=False)
    face_max_video_size_mb = fields.Integer(related="company_id.face_max_video_size_mb", readonly=False)
    face_ip_restriction_enabled = fields.Boolean(related="company_id.face_ip_restriction_enabled", readonly=False)
    face_allowed_ip_list = fields.Text(related="company_id.face_allowed_ip_list", readonly=False)
    face_blocked_ip_list = fields.Text(related="company_id.face_blocked_ip_list", readonly=False)
