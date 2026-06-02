from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    note = fields.Text()
    in_mode = fields.Selection(
        selection_add=[
            ("face_scan", "Face Scan"),
            ("has_not_checkout", "Has Not Checkout"),
        ],
        ondelete={
            "face_scan": "set default",
            "has_not_checkout": "set default",
        },
    )
