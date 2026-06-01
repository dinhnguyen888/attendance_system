import ipaddress
import os
import re

from odoo import fields, models
from odoo.http import request


class ResCompany(models.Model):
    _inherit = "res.company"

    face_ai_grpc_target = fields.Char(default=lambda self: os.getenv("FACE_AI_GRPC_TARGET", "localhost:50051"))
    face_default_threshold = fields.Float(default=0.5)
    face_min_valid_frames = fields.Integer(default=1)
    face_max_spoofing_error_rate = fields.Float(default=0.0)
    face_max_video_size_mb = fields.Integer(default=8)
    face_ip_restriction_enabled = fields.Boolean(default=False)
    face_allowed_ip_list = fields.Text(default="")
    face_blocked_ip_list = fields.Text(default="")

    def is_face_attendance_ip_allowed(self):
        self.ensure_one()
        if not self.face_ip_restriction_enabled:
            return True

        client_ip = self._face_attendance_client_ip()
        if not client_ip:
            return False

        blocked_networks = self._parse_face_attendance_ip_entries(self.face_blocked_ip_list)
        if self._ip_in_entries(client_ip, blocked_networks):
            return False

        allowed_networks = self._parse_face_attendance_ip_entries(self.face_allowed_ip_list)
        if not allowed_networks:
            return True
        return self._ip_in_entries(client_ip, allowed_networks)

    @staticmethod
    def _face_attendance_client_ip():
        forwarded_for = request.httprequest.headers.get("X-Forwarded-For", "")
        raw_ip = forwarded_for.split(",", 1)[0].strip() or request.httprequest.remote_addr
        try:
            return ipaddress.ip_address(raw_ip)
        except ValueError:
            return None

    @staticmethod
    def _parse_face_attendance_ip_entries(value):
        entries = []
        for token in re.split(r"[\s,;]+", value or ""):
            token = token.strip()
            if not token:
                continue
            try:
                entries.append(ipaddress.ip_network(token, strict=False))
            except ValueError:
                continue
        return entries

    @staticmethod
    def _ip_in_entries(client_ip, entries):
        return any(client_ip.version == entry.version and client_ip in entry for entry in entries)
