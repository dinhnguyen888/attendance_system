from odoo import models, fields, api, _

class LeaveRequestRejectWizard(models.TransientModel):
    _name = 'leave.request.reject.wizard'
    _description = 'Wizard từ chối đơn nghỉ phép'

    leave_request_id = fields.Many2one('leave.request', string='Đơn nghỉ phép', required=True)
    rejection_reason = fields.Text('Lý do từ chối', required=True)

    def action_reject(self):
        for wizard in self:
            wizard.leave_request_id.write({
                'state': 'rejected',
                'rejection_reason': wizard.rejection_reason
            })
            wizard.leave_request_id._safe_message_post(
                f"Đơn nghỉ phép đã bị từ chối. Lý do: {wizard.rejection_reason}",
                'notification',
                'mail.mt_comment'
            )
        return {'type': 'ir.actions.act_window_close'}
