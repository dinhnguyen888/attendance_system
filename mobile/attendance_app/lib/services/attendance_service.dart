import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../constants/app_constants.dart';
import '../models/attendance.dart';
import 'api_service.dart';

class AttendanceService {
  static final AttendanceService _instance = AttendanceService._internal();
  factory AttendanceService() => _instance;
  AttendanceService._internal();

  final ApiService _apiService = ApiService();

  Future<Map<String, dynamic>> checkIn({
    required File faceImage,
    String? wifiIp,
  }) async {
    try {
      final faceImageData =
          'data:image/jpeg;base64,${await _fileToBase64(faceImage)}';

      final params = {
        "face_image": faceImageData,
      };

      if (wifiIp != null && wifiIp.isNotEmpty) {
        params["wifi_ip"] = wifiIp;
      }

      final checkInData = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": params,
      };

      final response = await http
          .post(
            Uri.parse(
                '${AppConstants.baseUrl}${AppConstants.odooAttendanceCheckInEndpoint}'),
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'Cookie': 'session_id=${_apiService.sessionId}',
            },
            body: jsonEncode(checkInData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['result'] != null) {
          if (data['result']['success'] == true) {
            return {
              'success': true,
              'message': 'Check-in thành công',
              'attendance_id': data['result']['attendance_id'],
              'check_in_time': data['result']['check_in_time'],
              'confidence': data['result']['confidence'] ?? 0.0,
            };
          } else {
            return {
              'success': false,
              'message': data['result']['error'] ?? 'Check-in thất bại',
            };
          }
        } else if (data['error'] != null) {
          return {
            'success': false,
            'message': data['error']['message'] ??
                data['error']['data']['message'] ??
                'Lỗi không xác định',
          };
        }
      }
      return {'success': false, 'message': 'Lỗi kết nối server'};
    } catch (e) {
      return {'success': false, 'message': 'Lỗi: $e'};
    }
  }

  Future<Map<String, dynamic>> checkOut({
    required File faceImage,
    String? wifiIp,
  }) async {
    try {
      final faceImageData =
          'data:image/jpeg;base64,${await _fileToBase64(faceImage)}';

      final params = {
        "face_image": faceImageData,
      };

      if (wifiIp != null && wifiIp.isNotEmpty) {
        params["wifi_ip"] = wifiIp;
      }

      final checkOutData = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": params,
      };

      final response = await http
          .post(
            Uri.parse(
                '${AppConstants.baseUrl}${AppConstants.odooAttendanceCheckOutEndpoint}'),
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'Cookie': 'session_id=${_apiService.sessionId}',
            },
            body: jsonEncode(checkOutData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['result'] != null) {
          if (data['result']['success'] == true) {
            return {
              'success': true,
              'message': 'Check-out thành công',
              'attendance_id': data['result']['attendance_id'],
              'check_out_time': data['result']['check_out_time'],
              'work_hours': data['result']['work_hours'] ?? 0.0,
              'confidence': data['result']['confidence'] ?? 0.0,
            };
          } else {
            return {
              'success': false,
              'message': data['result']['error'] ?? 'Check-out thất bại',
            };
          }
        } else if (data['error'] != null) {
          return {
            'success': false,
            'message': data['error']['message'] ??
                data['error']['data']['message'] ??
                'Lỗi không xác định',
          };
        }
      }
      return {'success': false, 'message': 'Lỗi kết nối server'};
    } catch (e) {
      return {'success': false, 'message': 'Lỗi: $e'};
    }
  }

  Future<AttendanceStatus> getStatus() async {
    try {
      if (_apiService.sessionId == null) {
        throw Exception('Session không hợp lệ, vui lòng đăng nhập lại');
      }

      final statusData = {"jsonrpc": "2.0", "method": "call", "params": {}};

      final response = await http
          .post(
            Uri.parse(
                '${AppConstants.baseUrl}${AppConstants.odooAttendanceStatusEndpoint}'),
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'Cookie': 'session_id=${_apiService.sessionId}',
            },
            body: jsonEncode(statusData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['result'] != null) {
          final result = data['result'];
          if (result['error'] != null) {
            throw Exception(result['error']);
          }
          return AttendanceStatus(
            status: result['status'] ?? 'unknown',
            message: result['message'] ?? '',
            checkIn: result['check_in_time'],
            checkOut: result['check_out_time'],
            totalHours: result['work_hours']?.toDouble() ?? 0.0,
            canCheckIn: result['can_check_in'] ?? false,
            canCheckOut: result['can_check_out'] ?? false,
            needRegister: result['need_register'] ?? false,
          );
        } else if (data['error'] != null) {
          throw Exception(data['error']['data']['message'] ??
              data['error']['message'] ??
              'Lỗi không xác định');
        }
      }
      throw Exception('Lỗi kết nối server: ${response.statusCode}');
    } catch (e) {
      throw Exception('Lỗi mạng: $e');
    }
  }

  Future<String> _fileToBase64(File file) async {
    final bytes = await file.readAsBytes();
    return base64Encode(bytes);
  }
}
