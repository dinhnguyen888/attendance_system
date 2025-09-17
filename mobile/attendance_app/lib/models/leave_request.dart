class LeaveRequest {
  final int id;
  final int employeeId;
  final String name;
  final String leaveType;
  final String startDate;
  final String endDate;
  final double daysRequested;
  final String reason;
  final String state;
  final String? managerApprovalDate;
  final String? hrApprovalDate;
  final String? rejectionReason;
  final String createDate;

  LeaveRequest({
    required this.id,
    required this.employeeId,
    required this.name,
    required this.leaveType,
    required this.startDate,
    required this.endDate,
    required this.daysRequested,
    required this.reason,
    required this.state,
    this.managerApprovalDate,
    this.hrApprovalDate,
    this.rejectionReason,
    required this.createDate,
  });

  factory LeaveRequest.fromJson(Map<String, dynamic> json) {
    return LeaveRequest(
      id: json['id'] ?? 0,
      employeeId: json['employee_id'] ?? 0,
      name: json['name']?.toString() ?? '',
      leaveType: json['leave_type']?.toString() ?? '',
      startDate: json['start_date']?.toString() ?? '',
      endDate: json['end_date']?.toString() ?? '',
      daysRequested: (json['days_requested'] ?? 0.0).toDouble(),
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
      'leave_type': leaveType,
      'start_date': startDate,
      'end_date': endDate,
      'days_requested': daysRequested,
      'reason': reason,
      'state': state,
      'manager_approval_date': managerApprovalDate,
      'hr_approval_date': hrApprovalDate,
      'rejection_reason': rejectionReason,
      'create_date': createDate,
    };
  }
}

class LeaveRequestCreate {
  final String leaveType;
  final String startDate;
  final String endDate;
  final String reason;

  LeaveRequestCreate({
    required this.leaveType,
    required this.startDate,
    required this.endDate,
    required this.reason,
  });

  Map<String, dynamic> toJson() {
    return {
      'leave_type': leaveType,
      'start_date': startDate,
      'end_date': endDate,
      'reason': reason,
    };
  }
}

class LeaveType {
  final String value;
  final String label;

  LeaveType({
    required this.value,
    required this.label,
  });

  static List<LeaveType> getLeaveTypes() {
    return [
      LeaveType(value: 'annual', label: 'Nghỉ phép năm'),
      LeaveType(value: 'sick', label: 'Nghỉ ốm'),
      LeaveType(value: 'personal', label: 'Nghỉ cá nhân'),
      LeaveType(value: 'maternity', label: 'Nghỉ thai sản'),
      LeaveType(value: 'paternity', label: 'Nghỉ thai sản (nam)'),
      LeaveType(value: 'unpaid', label: 'Nghỉ không lương'),
    ];
  }
}
