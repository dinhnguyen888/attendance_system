from odoo import api, fields, models
from odoo.http import request

from .hr_employee import HrEmployee
from ..grpc.face_ai_client import FaceAiClient


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def verify_face_scan_bytes(self, video_bytes, video_mime="video/webm"):
        registered_employees = self._face_scan_registered_employees()
        if not registered_employees:
            return self._face_scan_error("No registered face profiles are available.")

        companies = registered_employees.mapped("company_id")
        max_size = max(max(1, int(company.face_max_video_size_mb)) for company in companies) * 1024 * 1024

        if not video_bytes or len(video_bytes) > max_size:
            return self._face_scan_error("Invalid verification video.")

        candidates = self._build_face_candidates(registered_employees)
        if not candidates:
            return self._face_scan_error("No registered face profiles are available.")

        try:
            response = FaceAiClient(self._face_scan_ai_target(companies)).analyze_face(
                video_bytes=video_bytes,
                video_mime=video_mime or "video/webm",
                candidates=candidates,
                max_frames=7,
            )
        except Exception:
            return self._face_scan_error("Face verification service is unavailable.")

        if response.status != "OK":
            return self._face_scan_error("Unable to analyze face.")

        match = self._select_face_scan_match(response, candidates)
        if not match:
            return self._face_scan_error("Unable to verify face.")

        user = self.sudo().browse(match["user_id"])
        if not user.exists() or not user.active or user.share:
            return self._face_scan_error("Unable to verify face.")

        employee = self.env["hr.employee"].sudo().browse(match["employee_id"])
        if not employee.exists() or employee.user_id != user:
            return self._face_scan_error("Unable to verify face.")

        self._check_in_face_scan_employee(employee)
        self._login_face_scan_user(user)
        return {
            "ok": True,
            "message": "Login successful.",
            "redirect_url": "/odoo",
        }

    @api.model
    def _face_scan_registered_employees(self):
        employees = self.env["hr.employee"].sudo().search([
            ("user_id", "!=", False),
            ("user_id.active", "=", True),
            ("user_id.share", "=", False),
            ("image_1920", "!=", False),
            ("is_face_registered", "=", True),
            ("face_embedding", "!=", False),
        ])
        return employees.filtered(lambda employee: employee.company_id and employee.company_id.is_face_attendance_ip_allowed())

    @api.model
    def _face_scan_ai_target(self, companies):
        company = companies.filtered("face_ai_grpc_target")[:1]
        return company.face_ai_grpc_target if company else ""

    @api.model
    def _build_face_candidates(self, employees):
        candidates = []
        seen_employees = set()
        for employee in employees:
            if not employee.user_id or employee.id in seen_employees:
                continue
            embedding = HrEmployee.decode_face_embedding(employee.face_embedding)
            if not embedding:
                continue
            candidates.append({
                "user_id": employee.user_id.id,
                "employee_id": employee.id,
                "company_id": employee.company_id.id,
                "registered_embedding": embedding,
                "threshold": float(employee.company_id.face_default_threshold),
                "min_valid_frames": max(1, int(employee.company_id.face_min_valid_frames)),
                "max_spoofing_error_rate": float(employee.company_id.face_max_spoofing_error_rate),
            })
            seen_employees.add(employee.id)
        return candidates

    @api.model
    def _select_face_scan_match(self, response, candidates):
        candidates_by_employee = {
            int(candidate["employee_id"]): candidate
            for candidate in candidates
        }

        matches = [
            candidate for candidate in response.candidates
            if candidate.max_similarity >= candidate.threshold
        ]
        if len(matches) != 1:
            return False

        match = matches[0]
        candidate = candidates_by_employee.get(int(match.employee_id))
        if not candidate:
            return False
        if response.valid_frame_count < candidate["min_valid_frames"]:
            return False
        if response.spoofing_error_rate > candidate["max_spoofing_error_rate"]:
            return False
        return {
            "user_id": int(match.user_id),
            "employee_id": int(match.employee_id),
            "company_id": int(candidate["company_id"]),
        }

    @api.model
    def _login_face_scan_user(self, user):
        request.session["pre_login"] = user.login
        request.session["pre_uid"] = user.id
        request.session.finalize(self.env)
        request.update_env(user=user.id)
        self.env.cr.commit()

    @api.model
    def _check_in_face_scan_employee(self, employee):
        open_attendance = self.env["hr.attendance"].sudo().search([
            ("employee_id", "=", employee.id),
            ("check_out", "=", False),
        ], limit=1)
        if open_attendance:
            return open_attendance

        return self.env["hr.attendance"].sudo().create({
            "employee_id": employee.id,
            "check_in": fields.Datetime.now(),
            "in_mode": "face_scan",
            "in_ip_address": self._face_scan_client_ip(),
            "in_browser": request.httprequest.user_agent.string,
            "note": "Checked in by face scan login.",
        })

    @staticmethod
    def _face_scan_client_ip():
        forwarded_for = request.httprequest.headers.get("X-Forwarded-For", "")
        return forwarded_for.split(",", 1)[0].strip() or request.httprequest.remote_addr

    @staticmethod
    def _face_scan_error(message):
        return {
            "ok": False,
            "message": message,
        }
