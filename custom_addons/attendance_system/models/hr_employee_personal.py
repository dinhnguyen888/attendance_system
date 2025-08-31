from odoo import models, fields

class HrEmployeePersonal(models.Model):
    _name = 'hr.employee.personal'
    _description = 'Thông tin cá nhân nhân viên'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Xem thông tin chi tiết:', required=True, ondelete='cascade')
    
    # Thông tin cơ bản từ hr.employee
    name = fields.Char(related='employee_id.name', string='Tên nhân viên', readonly=True)
    work_phone = fields.Char(related='employee_id.work_phone', string='Điện thoại công ty', readonly=True)
    work_email = fields.Char(related='employee_id.work_email', string='Email công ty', readonly=True)
    mobile_phone = fields.Char(related='employee_id.mobile_phone', string='Điện thoại di động', readonly=True)
    job_title = fields.Char(related='employee_id.job_title', string='Chức vụ', readonly=True)
    department_id = fields.Many2one(related='employee_id.department_id', string='Phòng ban', readonly=True)
    

