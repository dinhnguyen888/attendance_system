from odoo import http
from odoo.addons.web.controllers.utils import ensure_db
from odoo.http import request


class RespFaceLoginController(http.Controller):
    @http.route(
        "/resp_face_attendance/face_login/verify",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=True,
    )
    def verify_face_login(self, **kwargs):
        ensure_db()
        users = request.env["res.users"].sudo()
        if not users._face_scan_registered_employees():
            return request.make_json_response({
                "ok": False,
                "message": "No registered face profiles are available from this network.",
            })

        upload = request.httprequest.files.get("face_video")
        if not upload:
            return request.make_json_response({
                "ok": False,
                "message": "No verification video received.",
            })

        return request.make_json_response(
            users.verify_face_scan_bytes(
                upload.read(),
                upload.content_type or "video/webm",
            )
        )
