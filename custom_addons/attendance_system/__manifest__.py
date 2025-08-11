{
    'name': 'Attendance System Customized',
    'version': '1.0',
    'summary': 'Chấm công bằng nhận diện khuôn mặt',
    'author': 'Đỉnh + Huy + Khánh',
    'depends': ['hr', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_view.xml',
    ],
    'application': True,
}
