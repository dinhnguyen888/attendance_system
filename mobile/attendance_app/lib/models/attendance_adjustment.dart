class AttendanceAdjustment {
  final int id;
  final int employeeId;
  final String name;
  final String date;
  final String? originalCheckIn;
  final String? originalCheckOut;
  final String? requestedCheckIn;
  final String? requestedCheckOut;
  final String reason;
  final String state;
  final String? managerApprovalDate;
  final String? hrApprovalDate;
  final String? rejectionReason;
  final String createDate;

  AttendanceAdjustment({
    required this.id,
    required this.employeeId,
    required this.name,
    required this.date,
    this.originalCheckIn,
    this.originalCheckOut,
    this.requestedCheckIn,
    this.requestedCheckOut,
    required this.reason,
    required this.state,
    this.managerApprovalDate,
    this.hrApprovalDate,
    this.rejectionReason,
    required this.createDate,
  });

  factory AttendanceAdjustment.fromJson(Map<String, dynamic> json) {
    return AttendanceAdjustment(
      id: json['id'] ?? 0,
      employeeId: json['employee_id'] ?? 0,
      name: json['name']?.toString() ?? '',
      date: json['date']?.toString() ?? '',
      originalCheckIn: json['original_check_in']?.toString(),
      originalCheckOut: json['original_check_out']?.toString(),
      requestedCheckIn: json['requested_check_in']?.toString(),
      requestedCheckOut: json['requested_check_out']?.toString(),
      reason: json['reason']?.toString() ?? '',
      state: json['state']?.toString() ?? '',
      managerApprovalDate: json['manager_approval_date']?.toString(),
      hrApprovalDate: json['hr_approval_date']?.toString(),
      rejectionReason: json['rejection_reason']?.toString(),
      createDate: json['create_date']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'employee_id': employeeId,
      'name': name,
      'date': date,
      'original_check_in': originalCheckIn,
      'original_check_out': originalCheckOut,
      'requested_check_in': requestedCheckIn,
      'requested_check_out': requestedCheckOut,
      'reason': reason,
      'state': state,
      'manager_approval_date': managerApprovalDate,
      'hr_approval_date': hrApprovalDate,
      'rejection_reason': rejectionReason,
      'create_date': createDate,
    };
  }
}

class AttendanceAdjustmentCreate {
  final String date;
  final String? originalCheckIn;
  final String? originalCheckOut;
  final String? requestedCheckIn;
  final String? requestedCheckOut;
  final String reason;

  AttendanceAdjustmentCreate({
    required this.date,
    this.originalCheckIn,
    this.originalCheckOut,
    this.requestedCheckIn,
    this.requestedCheckOut,
    required this.reason,
  });

  Map<String, dynamic> toJson() {
    return {
      'date': date,
      'original_check_in': originalCheckIn,
      'original_check_out': originalCheckOut,
      'requested_check_in': requestedCheckIn,
      'requested_check_out': requestedCheckOut,
      'reason': reason,
    };
  }
}
