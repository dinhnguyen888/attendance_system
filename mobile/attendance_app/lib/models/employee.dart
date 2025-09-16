class Employee {
  final int id;
  final String name;
  final String employeeCode;
  final String department;
  final String position;
  final String email;
  final String phone;
  final bool faceRegistered;
  final String? lastAttendance;
  final String? manager;
  final String? startDate;

  Employee({
    required this.id,
    required this.name,
    required this.employeeCode,
    required this.department,
    required this.position,
    required this.email,
    required this.phone,
    required this.faceRegistered,
    this.lastAttendance,
    this.manager,
    this.startDate,
  });

  factory Employee.fromJson(Map<String, dynamic> json) {
    return Employee(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      employeeCode: json['employee_code'] ?? '',
      department: json['department'] ?? '',
      position: json['position'] ?? '',
      email: json['email'] ?? '',
      phone: json['phone'] ?? '',
      faceRegistered: json['face_registered'] ?? false,
      lastAttendance: json['last_attendance'],
      manager: json['manager'] ?? '',
      startDate: json['start_date'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'employee_code': employeeCode,
      'department': department,
      'position': position,
      'email': email,
      'phone': phone,
      'face_registered': faceRegistered,
      'last_attendance': lastAttendance,
      'manager': manager,
      'start_date': startDate,
    };
  }
}
