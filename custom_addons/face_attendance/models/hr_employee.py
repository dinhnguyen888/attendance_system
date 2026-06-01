import base64
import json

from odoo import api, fields, models

from ..grpc.face_ai_client import FaceAiClient


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_face_registered = fields.Boolean(default=False, readonly=True)
    face_embedding = fields.Binary(readonly=True, groups="hr.group_hr_user")
    face_embedding_dim = fields.Integer(readonly=True, groups="hr.group_hr_user")
    face_embedding_model = fields.Char(readonly=True, groups="hr.group_hr_user")
    face_embedding_version = fields.Char(readonly=True, groups="hr.group_hr_user")
    face_registered_at = fields.Datetime(readonly=True, groups="hr.group_hr_user")
    face_register_status = fields.Selection(
        [
            ("none", "None"),
            ("success", "Success"),
            ("failed", "Failed"),
            ("skipped", "Skipped"),
        ],
        default="none",
        readonly=True,
        groups="hr.group_hr_user",
    )
    face_register_message = fields.Char(readonly=True, groups="hr.group_hr_user")

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        if not self.env.context.get("_skip_face_registration"):
            employees._register_face_from_employee_image()
        return employees

    def write(self, vals):
        res = super().write(vals)
        if (
            not self.env.context.get("_skip_face_registration")
            and ("image_1920" in vals or "user_id" in vals)
        ):
            self._register_face_from_employee_image()
        return res

    def _face_ai_client(self):
        company = self.company_id or self.env.company
        return FaceAiClient(company.face_ai_grpc_target)

    @staticmethod
    def _decode_binary(binary_value):
        if not binary_value:
            return b""
        if isinstance(binary_value, str):
            binary_value = binary_value.encode()
        try:
            return base64.b64decode(binary_value)
        except Exception:
            return b""

    @staticmethod
    def _encode_embedding(values):
        payload = json.dumps([float(value) for value in values]).encode()
        return base64.b64encode(payload)

    @staticmethod
    def decode_face_embedding(binary_value):
        raw = HrEmployee._decode_binary(binary_value)
        if not raw:
            return []
        try:
            return [float(value) for value in json.loads(raw.decode())]
        except Exception:
            return []

    def _register_face_from_employee_image(self):
        for employee in self.sudo():
            image_bytes = self._decode_binary(employee.image_1920)
            if not image_bytes:
                employee.with_context(_skip_face_registration=True).write({
                    "is_face_registered": False,
                    "face_register_status": "skipped",
                    "face_register_message": "Employee has no image_1920",
                })
                continue
            if image_bytes.lstrip().startswith(b"<svg"):
                employee.with_context(_skip_face_registration=True).write({
                    "is_face_registered": False,
                    "face_register_status": "skipped",
                    "face_register_message": "Generated SVG avatar skipped",
                })
                continue

            try:
                response = employee._face_ai_client().register_face(
                    employee.id,
                    image_bytes,
                    "image/png",
                )
            except Exception as exc:
                employee.with_context(_skip_face_registration=True).write({
                    "face_register_status": "failed",
                    "face_register_message": "AI service unavailable: %s" % exc,
                })
                continue

            if response.status == "OK" and response.embedding:
                employee.with_context(_skip_face_registration=True).write({
                    "is_face_registered": True,
                    "face_embedding": self._encode_embedding(response.embedding),
                    "face_embedding_dim": response.embedding_dim,
                    "face_embedding_model": response.model_name,
                    "face_embedding_version": "v1",
                    "face_registered_at": fields.Datetime.now(),
                    "face_register_status": "success",
                    "face_register_message": response.message,
                })
            else:
                values = {
                    "face_register_status": "failed",
                    "face_register_message": response.message or response.error_code,
                }
                if not employee.face_embedding:
                    values["is_face_registered"] = False
                employee.with_context(_skip_face_registration=True).write(values)
