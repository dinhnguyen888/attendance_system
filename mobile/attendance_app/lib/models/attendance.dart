class Attendance {
  final int id;
  final int employeeId;
  final String? checkIn;
  final String? checkOut;
  final String date;
  final double? totalHours;
  final String status;
  final double? verificationConfidence;
  final String? verificationMessage;
  final String? wifiIp;
  final bool? wifiValidated;
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
    this.verificationConfidence,
    this.verificationMessage,
    this.wifiIp,
    this.wifiValidated,
    this.overTime,
    this.checkInMode,
    this.checkOutMode,
    this.faceImage,
  });

  factory Attendance.fromJson(Map<String, dynamic> json) {
    try {
      return Attendance(
        id: json['id'] ?? 0,
        employeeId: json['employee_id'] ?? 0,
        checkIn: json['check_in']?.toString(),
        checkOut: json['check_out']?.toString(),
        date: json['date']?.toString() ?? '',
        totalHours: json['total_hours'] is num
            ? json['total_hours'].toDouble()
            : double.tryParse(json['total_hours']?.toString() ?? '0') ?? 0.0,
        status: json['status']?.toString() ?? '',
        verificationConfidence: json['verification_confidence'] is num
            ? json['verification_confidence'].toDouble()
            : double.tryParse(
                json['verification_confidence']?.toString() ?? '0'),
        verificationMessage: json['verification_message']?.toString(),
        wifiIp: json['wifi_ip']?.toString(),
        wifiValidated: json['wifi_validated'] is bool
            ? json['wifi_validated']
            : (json['wifi_validated']?.toString().toLowerCase() == 'true'),
        overTime: json['over_time']?.toString(),
        checkInMode: json['check_in_mode']?.toString(),
        checkOutMode: json['check_out_mode']?.toString(),
        faceImage: json['face_image']?.toString(),
      );
    } catch (e) {
      print('❌ Parse error: $e');
      rethrow;
    }
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
      'verification_confidence': verificationConfidence,
      'verification_message': verificationMessage,
      'wifi_ip': wifiIp,
      'wifi_validated': wifiValidated,
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
  final bool canCheckIn;
  final bool canCheckOut;
  final bool needRegister;

  AttendanceStatus({
    required this.status,
    required this.message,
    this.checkIn,
    this.checkOut,
    required this.totalHours,
    this.canCheckIn = false,
    this.canCheckOut = false,
    this.needRegister = false,
  });

  factory AttendanceStatus.fromJson(Map<String, dynamic> json) {
    return AttendanceStatus(
      status: json['status'] ?? '',
      message: json['message'] ?? '',
      checkIn: json['check_in_time'],
      checkOut: json['check_out_time'],
      totalHours: (json['total_hours'] ?? 0.0).toDouble(),
      canCheckIn: json['can_check_in'] ?? false,
      canCheckOut: json['can_check_out'] ?? false,
      needRegister: json['need_register'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'status': status,
      'message': message,
      'check_in_time': checkIn,
      'check_out_time': checkOut,
      'total_hours': totalHours,
      'can_check_in': canCheckIn,
      'can_check_out': canCheckOut,
      'need_register': needRegister,
    };
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
