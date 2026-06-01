{
    "name": "Face Attendance",
    "version": "1.0.4",
    "category": "Human Resources",
    "summary": "Face login and face embedding registration for employees",
    "depends": ["base", "web", "hr_attendance"],
    "data": [
        "views/login_templates.xml",
        "views/hr_employee_views.xml",
        "views/hr_attendance_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "face_attendance/static/src/js/face_login.js",
            "face_attendance/static/src/scss/face_login.scss",
        ],
    },
    "external_dependencies": {
        "python": ["grpcio", "protobuf"],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
