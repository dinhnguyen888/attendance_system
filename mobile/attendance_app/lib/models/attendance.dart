class Attendance {
  final int id;
  final int employeeId;
  final String? checkIn;
  final String? checkOut;
  final String date;
  final double? totalHours;
  final String status;
  final double? authenticationReliability;
  final String? wifiName;
  final bool? validWifi;
  final String? overTime;
  final String? checkInMode;
  final String? checkOutMode;
  final String? faceImage;

  Attendance({
    required this.id,
    required this.employeeId,
    this.checkIn,
    this.checkOut,
    required this.date,
    this.totalHours,
    required this.status,
    this.authenticationReliability,
    this.wifiName,
    this.validWifi,
    this.overTime,
    this.checkInMode,
    this.checkOutMode,
    this.faceImage,
  });

  factory Attendance.fromJson(Map<String, dynamic> json) {
    return Attendance(
      id: json['id'] ?? 0,
      employeeId: json['employee_id'] ?? 0,
      checkIn: json['check_in'],
      checkOut: json['check_out'],
      date: json['date'] ?? '',
      totalHours: json['total_hours']?.toDouble(),
      status: json['status'] ?? '',
      authenticationReliability: json['authentication_reliability']?.toDouble(),
      wifiName: json['wifi_name'],
      validWifi: json['valid_wifi'],
      overTime: json['over_time'],
      checkInMode: json['check_in_mode'],
      checkOutMode: json['check_out_mode'],
      faceImage: json['face_image'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'employee_id': employeeId,
      'check_in': checkIn,
      'check_out': checkOut,
      'date': date,
      'total_hours': totalHours,
      'status': status,
      'authentication_reliability': authenticationReliability,
      'wifi_name': wifiName,
      'valid_wifi': validWifi,
      'over_time': overTime,
      'check_in_mode': checkInMode,
      'check_out_mode': checkOutMode,
      'face_image': faceImage,
    };
  }
}

class AttendanceStatus {
  final String status;
  final String message;
  final String? checkIn;
  final String? checkOut;
  final double totalHours;

  AttendanceStatus({
    required this.status,
    required this.message,
    this.checkIn,
    this.checkOut,
    required this.totalHours,
  });

  factory AttendanceStatus.fromJson(Map<String, dynamic> json) {
    return AttendanceStatus(
      status: json['status'] ?? '',
      message: json['message'] ?? '',
      checkIn: json['check_in'],
      checkOut: json['check_out'],
      totalHours: (json['total_hours'] ?? 0.0).toDouble(),
    );
  }
}

class AttendanceRequest {
  final int employeeId;
  final String action;
  final String? faceImage;
  final double? latitude;
  final double? longitude;
  final String? wifiName;
  final bool? validWifi;
  final String? deviceInfo;

  AttendanceRequest({
    required this.employeeId,
    required this.action,
    this.faceImage,
    this.latitude,
    this.longitude,
    this.wifiName,
    this.validWifi,
    this.deviceInfo,
  });

  Map<String, dynamic> toJson() {
    return {
      'employee_id': employeeId,
      'action': action,
      if (faceImage != null) 'face_image': faceImage,
      if (latitude != null) 'latitude': latitude,
      if (longitude != null) 'longitude': longitude,
      if (wifiName != null) 'wifi_name': wifiName,
      if (validWifi != null) 'valid_wifi': validWifi,
      if (deviceInfo != null) 'device_info': deviceInfo,
    };
  }
}
