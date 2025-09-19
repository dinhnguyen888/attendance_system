from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError
from datetime import datetime, time, timedelta

class WorkShift(models.Model):
    _name = 'work.shift'
    _description = 'Ca làm việc'
    _order = 'start_time'
    _active_name = 'active'
    name = fields.Char('Tên ca', required=True)
    start_time = fields.Float('Giờ bắt đầu', required=True)
    end_time = fields.Float('Giờ kết thúc', required=True)
    break_duration = fields.Float('Thời gian nghỉ (giờ)', default=1.0)
    work_duration = fields.Float('Thời gian làm việc (giờ)', compute='_compute_work_duration', store=True)
    is_overtime_eligible = fields.Boolean('Được tính làm thêm giờ', default=True)
    active = fields.Boolean('Đang hoạt động', default=True)
    description = fields.Text('Mô tả')
    
    @api.depends('start_time', 'end_time', 'break_duration')
    def _compute_work_duration(self):
        for shift in self:
            if shift.start_time and shift.end_time:
                total_hours = shift.end_time - shift.start_time
                shift.work_duration = max(0, total_hours - shift.break_duration)
            else:
                shift.work_duration = 0

    @api.constrains('start_time', 'end_time')
    def _check_time_validity(self):
        for shift in self:
            if shift.start_time >= shift.end_time:
                raise ValidationError('Giờ kết thúc phải sau giờ bắt đầu')
            if shift.start_time < 0 or shift.start_time >= 24:
                raise ValidationError('Giờ bắt đầu không hợp lệ')
            if shift.end_time <= 0 or shift.end_time > 24:
                raise ValidationError('Giờ kết thúc không hợp lệ')

    def get_shift_times(self):
        start_hour = int(self.start_time)
        start_minute = int((self.start_time - start_hour) * 60)
        end_hour = int(self.end_time)
        end_minute = int((self.end_time - end_hour) * 60)
        
        return {
            'start': time(start_hour, start_minute),
            'end': time(end_hour, end_minute)
        }

class EmployeeWorkSchedule(models.Model):
    _name = 'employee.work.schedule'
    _description = 'Lịch làm việc nhân viên'
    _order = 'date desc'

    employee_id = fields.Many2one('hr.employee', 'Nhân viên', required=True)
    shift_id = fields.Many2one('work.shift', 'Ca làm việc', required=True)
    date = fields.Date('Ngày', required=True)
    is_holiday = fields.Boolean('Ngày nghỉ', default=False)
    is_weekend = fields.Boolean('Cuối tuần', compute='_compute_is_weekend', store=True)
    notes = fields.Text('Ghi chú')
    
    @api.depends('date')
    def _compute_is_weekend(self):
        for schedule in self:
            if schedule.date:
                schedule.is_weekend = schedule.date.weekday() >= 5
            else:
                schedule.is_weekend = False

    @api.constrains('employee_id', 'date')
    def _check_unique_schedule(self):
        for schedule in self:
            existing = self.search([
                ('employee_id', '=', schedule.employee_id.id),
                ('date', '=', schedule.date),
                ('id', '!=', schedule.id)
            ])
            if existing:
                raise ValidationError(f'Nhân viên {schedule.employee_id.name} đã có lịch làm việc ngày {schedule.date}')

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    default_shift_id = fields.Many2one('work.shift', 'Ca làm việc mặc định')
    work_schedule_ids = fields.One2many('employee.work.schedule', 'employee_id', 'Lịch làm việc')
    
    def get_work_schedule(self, date):
        schedule = self.env['employee.work.schedule'].search([
            ('employee_id', '=', self.id),
            ('date', '=', date)
        ], limit=1)
        
        if schedule:
            return schedule.shift_id
        return self.default_shift_id

    def get_expected_work_hours(self, date):
        shift = self.get_work_schedule(date)
        if shift and shift.active and not self.env['employee.work.schedule'].search([
            ('employee_id', '=', self.id),
            ('date', '=', date),
            ('is_holiday', '=', True)
        ]):
            return shift.work_duration
        return 0

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    
    shift_id = fields.Many2one('work.shift', 'Ca làm việc', compute='_compute_shift_id', store=True)
    expected_work_hours = fields.Float('Số giờ làm việc dự kiến', compute='_compute_expected_work_hours', store=True)
    actual_work_hours = fields.Float('Số giờ làm việc thực tế', compute='_compute_actual_work_hours', store=True)
    overtime_hours = fields.Float('Số giờ làm thêm', compute='_compute_overtime_hours', store=True)
    late_minutes = fields.Integer('Số phút muộn', compute='_compute_late_minutes', store=True)
    early_leave_minutes = fields.Integer('Số phút về sớm', compute='_compute_early_leave_minutes', store=True)
    
    @api.depends('employee_id', 'check_in')
    def _compute_shift_id(self):
        for attendance in self:
            if attendance.employee_id and attendance.check_in:
                date = attendance.check_in.date()
                attendance.shift_id = attendance.employee_id.get_work_schedule(date)
            else:
                attendance.shift_id = False

    @api.depends('employee_id', 'check_in')
    def _compute_expected_work_hours(self):
        for attendance in self:
            if attendance.employee_id and attendance.check_in:
                date = attendance.check_in.date()
                attendance.expected_work_hours = attendance.employee_id.get_expected_work_hours(date)
            else:
                attendance.expected_work_hours = 0

    @api.depends('check_in', 'check_out')
    def _compute_actual_work_hours(self):
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                duration = attendance.check_out - attendance.check_in
                attendance.actual_work_hours = duration.total_seconds() / 3600
            else:
                attendance.actual_work_hours = 0

    @api.depends('expected_work_hours', 'actual_work_hours')
    def _compute_overtime_hours(self):
        for attendance in self:
            if attendance.expected_work_hours > 0:
                attendance.overtime_hours = max(0, attendance.actual_work_hours - attendance.expected_work_hours)
            else:
                attendance.overtime_hours = 0

    @api.depends('check_in', 'shift_id')
    def _compute_late_minutes(self):
        for attendance in self:
            if attendance.check_in and attendance.shift_id:
                check_in_time = attendance.check_in.time()
                shift_times = attendance.shift_id.get_shift_times()
                if check_in_time > shift_times['start']:
                    late_delta = datetime.combine(attendance.check_in.date(), check_in_time) - \
                               datetime.combine(attendance.check_in.date(), shift_times['start'])
                    attendance.late_minutes = int(late_delta.total_seconds() / 60)
                else:
                    attendance.late_minutes = 0
            else:
                attendance.late_minutes = 0

    @api.depends('check_out', 'shift_id')
    def _compute_early_leave_minutes(self):
        for attendance in self:
            if attendance.check_out and attendance.shift_id:
                check_out_time = attendance.check_out.time()
                shift_times = attendance.shift_id.get_shift_times()
                if check_out_time < shift_times['end']:
                    early_delta = datetime.combine(attendance.check_out.date(), shift_times['end']) - \
                                datetime.combine(attendance.check_out.date(), check_out_time)
                    attendance.early_leave_minutes = int(early_delta.total_seconds() / 60)
                else:
                    attendance.early_leave_minutes = 0
            else:
                attendance.early_leave_minutes = 0
