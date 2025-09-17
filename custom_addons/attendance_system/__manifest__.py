{
    'name': 'Attendance System Customized',
    'version': '1.2',
    'summary': 'Chấm công bằng nhận diện khuôn mặt',
    'description': """
        Hệ thống chấm công bằng nhận diện khuôn mặt sử dụng OpenCV.
        Tích hợp với custom API service để xác thực khuôn mặt.
        Bao gồm tính năng quản lý ảnh khuôn mặt cho nhân viên.
        Hỗ trợ mobile app với REST API.
    """,
    'author': 'Đỉnh + Huy + Khánh',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'hr_attendance',
        'web',
        'mail',
        'hr_holidays',
        'hr_timesheet',
        'hr_work_entry',
        'hr_contract',
    ],
    'external_dependencies': {
        'python': ['requests', 'PyJWT'],
    },
    'data': [
        'security/attendance_security.xml',
        'security/ir.model.access.csv',
        'views/attendance_adjustment_views.xml',
        'views/attendance_dashboard_views.xml',
        'views/attendance_dashboard_missing_views.xml',
        'views/attendance_view.xml',
        'views/employee_face_views.xml',
        'views/hr_employee_personal_views.xml',
        'views/attendance_config_views.xml',
        'views/work_shift_views.xml',
        'views/hr_employee_views.xml',
        'views/leave_request_views.xml',
        'data/leave_sequence.xml',
        'views/webcam_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'attendance_system/static/src/css/attendance.css',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
}
