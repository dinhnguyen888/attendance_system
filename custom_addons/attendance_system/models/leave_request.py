from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class LeaveRequest(models.Model):
    _name = 'leave.request'
    _description = 'Đơn nghỉ phép'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Mã đơn', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one('hr.department', string='Phòng ban', related='employee_id.department_id', store=True, readonly=True)
    manager_id = fields.Many2one('hr.employee', string='Quản lý trực tiếp', related='employee_id.parent_id', store=True, readonly=True)
    
    leave_type = fields.Selection([
        ('annual', 'Nghỉ phép năm'),
        ('sick', 'Nghỉ ốm'),
        ('personal', 'Nghỉ cá nhân'),
        ('maternity', 'Nghỉ thai sản'),
        ('paternity', 'Nghỉ thai sản (nam)'),
        ('unpaid', 'Nghỉ không lương'),
    ], string='Loại nghỉ phép', required=True, default='annual')
    
    start_date = fields.Date('Ngày bắt đầu', required=True)
    end_date = fields.Date('Ngày kết thúc', required=True)
    days_requested = fields.Float('Số ngày nghỉ', compute='_compute_days_requested', store=True)
    reason = fields.Text('Lý do nghỉ phép', required=True)
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Đã gửi'),
        ('manager_approved', 'Quản lý đã duyệt'),
        ('hr_approved', 'HR đã duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    ], string='Trạng thái', default='draft', tracking=True)
    
    manager_approval_date = fields.Datetime('Ngày duyệt quản lý', readonly=True)
    hr_approval_date = fields.Datetime('Ngày duyệt HR', readonly=True)
    rejection_reason = fields.Text('Lý do từ chối', readonly=True)
    
    @api.depends('start_date', 'end_date')
    def _compute_days_requested(self):
        for request in self:
            if request.start_date and request.end_date:
                if request.end_date < request.start_date:
                    request.days_requested = 0
                else:
                    delta = request.end_date - request.start_date
                    request.days_requested = delta.days + 1
            else:
                request.days_requested = 0

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('leave.request') or _('New')
        return super(LeaveRequest, self).create(vals)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for request in self:
            if request.start_date and request.end_date:
                if request.end_date < request.start_date:
                    raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu!')
                if request.start_date < fields.Date.today():
                    raise ValidationError('Không thể tạo đơn nghỉ phép cho ngày trong quá khứ!')

    def _safe_message_post(self, body, message_type='comment', subtype_xmlid='mail.mt_note'):
        try:
            self.with_context(mail_create_nosubscribe=True, mail_notify_force_send=False).message_post(
                body=body,
                message_type=message_type,
                subtype_xmlid=subtype_xmlid
            )
        except Exception as e:
            _logger.warning(f"Không thể gửi thông báo: {str(e)}")

    def action_submit(self):
        for request in self:
            if request.state != 'draft':
                raise ValidationError('Chỉ có thể gửi đơn từ trạng thái nháp!')
            
            request.state = 'submitted'
            request._safe_message_post(
                f"Đơn nghỉ phép đã được gửi chờ duyệt từ quản lý trực tiếp.",
                'notification',
                'mail.mt_comment'
            )

    def action_manager_approve(self):
        for request in self:
            if request.state != 'submitted':
                raise ValidationError('Chỉ có thể duyệt đơn từ trạng thái đã gửi!')
            
            if not self.env.user.has_group('attendance_system.group_attendance_department_manager'):
                raise AccessError('Bạn không có quyền duyệt đơn nghỉ phép!')
            
            request.state = 'manager_approved'
            request.manager_approval_date = fields.Datetime.now()
            request._safe_message_post(
                f"Đơn nghỉ phép đã được quản lý trực tiếp duyệt. Chờ duyệt từ HR.",
                'notification',
                'mail.mt_comment'
            )

    def action_hr_approve(self):
        for request in self:
            if request.state != 'manager_approved':
                raise ValidationError('Chỉ có thể duyệt đơn từ trạng thái quản lý đã duyệt!')
            
            if not self.env.user.has_group('attendance_system.group_attendance_hr'):
                raise AccessError('Bạn không có quyền duyệt đơn nghỉ phép!')
            
            request.state = 'hr_approved'
            request.hr_approval_date = fields.Datetime.now()
            request._safe_message_post(
                f"Đơn nghỉ phép đã được HR duyệt. Đơn đã được phê duyệt hoàn toàn.",
                'notification',
                'mail.mt_comment'
            )

    def action_approve(self):
        for request in self:
            if request.state not in ['submitted', 'manager_approved', 'hr_approved']:
                raise ValidationError('Không thể duyệt đơn trong trạng thái hiện tại!')
            
            if request.state == 'submitted':
                request.action_manager_approve()
            if request.state == 'manager_approved':
                request.action_hr_approve()
            
            request.state = 'approved'

    def action_reject(self):
        for request in self:
            if request.state not in ['submitted', 'manager_approved']:
                raise ValidationError('Chỉ có thể từ chối đơn từ trạng thái đã gửi hoặc quản lý đã duyệt!')
            
            return {
                'name': 'Từ chối đơn nghỉ phép',
                'type': 'ir.actions.act_window',
                'res_model': 'leave.request.reject.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_leave_request_id': request.id}
            }

    def action_configure_email(self):
        return {
            'name': 'Cấu hình Email',
            'type': 'ir.actions.act_window',
            'res_model': 'res.config.settings',
            'view_mode': 'form',
            'target': 'current',
            'context': {'module': 'base'}
        }

    def action_test_email_config(self):
        try:
            self.env['mail.mail'].create({
                'subject': 'Test Email Configuration',
                'body_html': '<p>Email configuration is working properly.</p>',
                'email_to': self.env.user.email,
                'email_from': self.env.user.email,
            }).send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thành công',
                    'message': 'Cấu hình email hoạt động bình thường!',
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': f'Lỗi cấu hình email: {str(e)}',
                    'type': 'danger',
                }
            }

    def name_get(self):
        result = []
        for request in self:
            result.append((request.id, f"{request.name} - {request.employee_id.name}"))
        return result
