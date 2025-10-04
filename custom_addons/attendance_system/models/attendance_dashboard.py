from odoo import models, fields, api
from datetime import datetime, timedelta, date


class AttendanceDashboard(models.TransientModel):
    _name = 'attendance.dashboard'
    _description = 'Dashboard chấm công nhanh'

    date_from = fields.Date(string='Từ ngày', default=lambda self: fields.Date.context_today(self))
    date_to = fields.Date(string='Đến ngày', default=lambda self: fields.Date.context_today(self))

    total_attendances = fields.Integer(string='Bản ghi', compute='_compute_kpis', compute_sudo=True)
    with_checkout = fields.Integer(string='Đã checkout', compute='_compute_kpis', compute_sudo=True)
    without_checkout = fields.Integer(string='Chưa checkout', compute='_compute_kpis', compute_sudo=True)
    employees_no_attendance = fields.Integer(string='NV chưa chấm công', compute='_compute_kpis', compute_sudo=True)
    total_missing_days = fields.Integer(string='Ngày thiếu công', compute='_compute_kpis', compute_sudo=True)

    missing_line_ids = fields.One2many('attendance.dashboard.missing', 'wizard_id', string='Thiếu công chi tiết')

    def _get_attendance_domain(self):
        user = self.env.user
        domain = []

        # Quyền xem theo nhóm
        if user.has_group('attendance_system.group_attendance_hr') or user.has_group('base.group_system'):
            pass
        elif user.has_group('attendance_system.group_attendance_department_manager'):
            domain += [('employee_id.department_id.manager_id.user_id', '=', user.id)]
        else:
            domain += [('id', '=', 0)]  # không cho nhân viên xem dashboard

        # Khoảng ngày theo check_in
        for wizard in self:
            # Lấy khoảng theo ngày (00:00 -> 23:59)
            date_from_dt = fields.Datetime.to_datetime(wizard.date_from)
            date_to_dt = fields.Datetime.to_datetime(wizard.date_to) + timedelta(days=1)
            domain += [('check_in', '>=', date_from_dt), ('check_in', '<', date_to_dt)]
        return domain

    @api.depends('date_from', 'date_to')
    def _compute_kpis(self):
        for wizard in self:
            # Gán mặc định để tránh lỗi compute nếu có ngoại lệ phía dưới
            wizard.total_attendances = 0
            wizard.with_checkout = 0
            wizard.without_checkout = 0
            wizard.employees_no_attendance = 0
            wizard.total_missing_days = 0
            try:
                domain = wizard._get_attendance_domain()
                attendances = self.env['hr.attendance'].search(domain)
                wizard.total_attendances = len(attendances)
                wizard.with_checkout = len(attendances.filtered(lambda a: a.check_out))
                wizard.without_checkout = len(attendances.filtered(lambda a: not a.check_out))

                # Phạm vi nhân viên theo quyền
                employee_domain = []
                user = self.env.user
                if user.has_group('attendance_system.group_attendance_hr') or user.has_group('base.group_system'):
                    pass
                elif user.has_group('attendance_system.group_attendance_department_manager'):
                    employee_domain += [('department_id.manager_id.user_id', '=', user.id)]
                else:
                    employee_domain += [('id', '=', 0)]

                employees = self.env['hr.employee'].search(employee_domain)
                attended_employee_ids = set(attendances.mapped('employee_id').ids)
                wizard.employees_no_attendance = len(employees.filtered(lambda e: e.id not in attended_employee_ids))

                # Tính tổng ngày thiếu công (Mon-Fri) mà không tạo dòng chi tiết
                d_from = fields.Date.to_date(wizard.date_from)
                d_to = fields.Date.to_date(wizard.date_to)
                workdays = list(wizard._workdays_in_range(d_from, d_to)) if d_from and d_to else []
                att_days_by_emp = {}
                for att in attendances:
                    day = fields.Date.to_date(att.check_in)
                    if day:
                        att_days_by_emp.setdefault(att.employee_id.id, set()).add(day)
                missing_total = 0
                for emp in employees:
                    existing = att_days_by_emp.get(emp.id, set())
                    for wd in workdays:
                        if wd not in existing:
                            missing_total += 1
                wizard.total_missing_days = missing_total
            except Exception:
                # giữ giá trị mặc định đã gán bên trên
                continue

    # Actions mở danh sách tương ứng
    def action_open_attendances(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bản ghi chấm công',
            'res_model': 'hr.attendance',
            'view_mode': 'tree,form',
            'domain': self._get_attendance_domain(),
        }

    def action_open_without_checkout(self):
        self.ensure_one()
        domain = self._get_attendance_domain() + [('check_out', '=', False)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chưa check-out',
            'res_model': 'hr.attendance',
            'view_mode': 'tree,form',
            'domain': domain,
        }

    def action_open_no_attendance_employees(self):
        self.ensure_one()
        # Nhân viên chưa có bản ghi trong khoảng thời gian
        domain_att = self._get_attendance_domain()
        attendances = self.env['hr.attendance'].search(domain_att)
        attended_ids = attendances.mapped('employee_id').ids

        employee_domain = []
        user = self.env.user
        if user.has_group('attendance_system.group_attendance_hr') or user.has_group('base.group_system'):
            pass
        elif user.has_group('attendance_system.group_attendance_department_manager'):
            employee_domain += [('department_id.manager_id.user_id', '=', user.id)]
        else:
            employee_domain += [('user_id', '=', user.id)]
        employee_domain += [('id', 'not in', attended_ids or [0])]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Nhân viên chưa chấm công',
            'res_model': 'hr.employee',
            'view_mode': 'tree,form',
            'domain': employee_domain,
        }

    def _workdays_in_range(self, d_from: date, d_to: date):
        current = d_from
        while current <= d_to:
            if current.weekday() < 5:  # Mon-Fri
                yield current
            current += timedelta(days=1)

    def _date_range(self, start_date, end_date):
        current = start_date
        while current <= end_date:
            yield current
            current += timedelta(days=1)

    def _compute_missing_lines(self, employees, attendances):
        self.ensure_one()
        self.missing_line_ids.sudo().unlink()
        att_days_by_emp = {}
        for att in attendances:
            day = fields.Date.to_date(att.check_in)
            if not day:
                continue
            att_days_by_emp.setdefault(att.employee_id.id, set()).add(day)

        d_from = fields.Date.to_date(self.date_from)
        d_to = fields.Date.to_date(self.date_to)
        missing_total = 0
        lines = []
        workdays = list(self._workdays_in_range(d_from, d_to))
        
        approved_leaves = self.env['leave.request'].search([
            ('state', 'in', ['hr_approved', 'approved']),
            ('start_date', '<=', d_to),
            ('end_date', '>=', d_from),
        ])
        leave_by_emp_date = {}
        for leave in approved_leaves:
            for single_date in self._date_range(leave.start_date, leave.end_date):
                if d_from <= single_date <= d_to:
                    leave_by_emp_date.setdefault(leave.employee_id.id, {})[single_date] = {
                        'reason': leave.reason,
                        'leave_type': leave.leave_type
                    }
        
        for emp in employees:
            existing = att_days_by_emp.get(emp.id, set())
            emp_leaves = leave_by_emp_date.get(emp.id, {})
            for wd in workdays:
                if wd not in existing:
                    missing_total += 1
                    leave_info = emp_leaves.get(wd, {})
                    lines.append({
                        'wizard_id': self.id,
                        'employee_id': emp.id,
                        'department_id': emp.department_id.id,
                        'date': wd,
                        'leave_reason': leave_info.get('reason', ''),
                        'leave_type': leave_info.get('leave_type', False),
                    })
        if lines:
            self.env['attendance.dashboard.missing'].sudo().create(lines)
        self.total_missing_days = missing_total

    def action_open_missing_days(self):
        self.ensure_one()
        domain = self._get_attendance_domain()
        attendances = self.env['hr.attendance'].search(domain)
        employee_domain = []
        user = self.env.user
        if user.has_group('attendance_system.group_attendance_hr') or user.has_group('base.group_system'):
            pass
        elif user.has_group('attendance_system.group_attendance_department_manager'):
            employee_domain += [('department_id.manager_id.user_id', '=', user.id)]
        else:
            employee_domain += [('id', '=', 0)]
        employees = self.env['hr.employee'].search(employee_domain)
        self._compute_missing_lines(employees, attendances)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ngày thiếu công',
            'res_model': 'attendance.dashboard.missing',
            'view_mode': 'tree',
            'domain': [('wizard_id', '=', self.id)],
            'target': 'current',
        }


class AttendanceDashboardMissing(models.TransientModel):
    _name = 'attendance.dashboard.missing'
    _description = 'Dòng ngày thiếu công'

    wizard_id = fields.Many2one('attendance.dashboard', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban', readonly=True)
    date = fields.Date(string='Ngày', required=True)
    leave_reason = fields.Text(string='Lý do nghỉ phép', readonly=True)
    leave_type = fields.Selection([
        ('annual', 'Nghỉ phép năm'),
        ('sick', 'Nghỉ ốm'),
        ('personal', 'Nghỉ cá nhân'),
        ('maternity', 'Nghỉ thai sản'),
        ('paternity', 'Nghỉ thai sản (nam)'),
        ('unpaid', 'Nghỉ không lương'),
    ], string='Loại nghỉ phép', readonly=True)


