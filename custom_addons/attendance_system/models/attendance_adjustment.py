from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError


class AttendanceAdjustment(models.Model):
    _name = 'attendance.adjustment'
    _description = 'Yêu cầu chỉnh công'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Số yêu cầu', default='New', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, tracking=True)
    requester_id = fields.Many2one('res.users', string='Người yêu cầu', default=lambda self: self.env.user, readonly=True)
    attendance_id = fields.Many2one('hr.attendance', string='Bản ghi chấm công', required=True, tracking=True)

    adjustment_type = fields.Selection([
        ('check_in', 'Sửa giờ check-in'),
        ('check_out', 'Sửa giờ check-out'),
        ('both', 'Sửa cả check-in và check-out'),
        ('other', 'Khác')
    ], string='Loại chỉnh công', required=True, default='both', tracking=True)

    requested_check_in = fields.Datetime(string='Giờ check-in đề xuất')
    requested_check_out = fields.Datetime(string='Giờ check-out đề xuất')

    reason = fields.Text(string='Lý do', required=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('waiting_manager', 'Chờ trưởng phòng'),
        ('waiting_hr', 'Chờ HR'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ], string='Trạng thái', default='draft', tracking=True)

    department_id = fields.Many2one(related='employee_id.department_id', string='Phòng ban', store=True, readonly=True)

    def _safe_message_post(self, body, message_type='comment', subtype_xmlid='mail.mt_note'):
        """Helper method để gửi message an toàn, tránh lỗi email configuration"""
        try:
            self.with_context(mail_create_nosubscribe=True, mail_notify_force_send=False).message_post(
                body=body,
                message_type=message_type,
                subtype_xmlid=subtype_xmlid
            )
        except Exception as e:
            # Log lỗi nhưng không làm gián đoạn quy trình
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"Không thể gửi thông báo: {str(e)}")

    def _check_submit_permission(self):
        user = self.env.user
        for rec in self:
            if user.has_group('attendance_system.group_attendance_employee'):
                if rec.employee_id.user_id.id != user.id:
                    raise AccessError('Bạn chỉ có thể gửi yêu cầu cho chính mình.')
            # Trưởng phòng và HR có thể gửi thay cho nhân viên trong phạm vi quyền của họ

    def action_submit(self):
        self._check_submit_permission()
        for rec in self:
            if rec.adjustment_type in ('check_in', 'both') and not rec.requested_check_in:
                raise UserError('Vui lòng nhập giờ check-in đề xuất.')
            if rec.adjustment_type in ('check_out', 'both') and not rec.requested_check_out:
                raise UserError('Vui lòng nhập giờ check-out đề xuất.')
            rec.state = 'waiting_manager'
            rec._safe_message_post('Yêu cầu chuyển sang trạng thái Chờ trưởng phòng.')
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if not self.env.user.has_group('attendance_system.group_attendance_hr') and not self.env.user.has_group('base.group_system'):
                raise AccessError('Chỉ HR/Admin mới được đặt lại về nháp.')
            rec.state = 'draft'
        return True

    def action_manager_approve(self):
        user = self.env.user
        for rec in self:
            # Cho phép: Trưởng phòng của phòng ban, HR Manager, hoặc Admin
            is_dept_manager_group = user.has_group('attendance_system.group_attendance_department_manager')
            is_hr_manager_group = user.has_group('attendance_system.group_attendance_hr') or user.has_group('hr.group_hr_manager')
            is_admin = user.has_group('base.group_system')

            if not (is_dept_manager_group or is_hr_manager_group or is_admin):
                raise AccessError('Bạn không có quyền duyệt bước Trưởng phòng.')

            # Nếu không phải HR/Admin thì phải là trưởng phòng của chính phòng ban nhân viên
            if not (is_hr_manager_group or is_admin):
                if not rec.department_id or rec.department_id.manager_id.user_id.id != user.id:
                    raise AccessError('Bạn chỉ có thể duyệt yêu cầu của nhân viên trong phòng ban mình quản lý.')
            rec.state = 'waiting_hr'
            rec._safe_message_post('Trưởng phòng đã duyệt. Chuyển sang Chờ HR.')
        return True

    def action_hr_approve(self):
        user = self.env.user
        for rec in self:
            if not (user.has_group('attendance_system.group_attendance_hr') or user.has_group('hr.group_hr_manager') or user.has_group('base.group_system')):
                raise AccessError('Chỉ HR/HR Manager/Admin được duyệt bước này.')
            # Áp dụng chỉnh công
            vals = {}
            if rec.adjustment_type in ('check_in', 'both') and rec.requested_check_in:
                vals['check_in'] = rec.requested_check_in
            if rec.adjustment_type in ('check_out', 'both') and rec.requested_check_out:
                vals['check_out'] = rec.requested_check_out
            if vals:
                rec.attendance_id.sudo().with_context(skip_attendance_validation=True).write(vals)
            rec.state = 'approved'
            rec._safe_message_post('HR đã duyệt và áp dụng chỉnh công.')
        return True

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
            rec._safe_message_post('Yêu cầu đã bị từ chối.')
        return True

    def action_configure_email(self):
        """Action để cấu hình email nếu cần thiết"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cấu hình Email',
            'res_model': 'res.config.settings',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'module': 'base',
                'default_name': 'Email Configuration'
            }
        }

    def action_test_email_config(self):
        """Kiểm tra cấu hình email"""
        try:
            # Kiểm tra xem có cấu hình email server không
            mail_server = self.env['ir.mail_server'].search([], limit=1)
            if not mail_server:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Cảnh báo',
                        'message': 'Chưa cấu hình email server. Vui lòng cấu hình trong Settings > Technical > Email > Outgoing Mail Servers',
                        'type': 'warning',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Thành công',
                        'message': f'Email server đã được cấu hình: {mail_server.name}',
                        'type': 'success',
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': f'Lỗi kiểm tra email: {str(e)}',
                    'type': 'danger',
                }
            }

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('attendance.adjustment') or 'New'
        return super().create(vals)


