import 'dart:convert';
import 'package:http/http.dart' as http;
import '../constants/app_constants.dart';
import '../models/attendance.dart';
import 'api_service.dart';

class CalendarService {
  static final CalendarService _instance = CalendarService._internal();
  factory CalendarService() => _instance;
  CalendarService._internal();

  final ApiService _apiService = ApiService();

  Future<List<Attendance>> getAttendanceHistory({
    String? startDate,
    String? endDate,
  }) async {
    try {
      if (_apiService.sessionId == null) {
        throw Exception('Session không hợp lệ, vui lòng đăng nhập lại');
      }

      final params = <String, dynamic>{};
      if (startDate != null) params['start_date'] = startDate;
      if (endDate != null) params['end_date'] = endDate;

      final requestData = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": params,
      };

      final response = await http
          .post(
            Uri.parse(
              '${AppConstants.baseUrl}${AppConstants.odooAttendanceHistoryEndpoint}',
            ),
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'Cookie': 'session_id=${_apiService.sessionId}',
            },
            body: jsonEncode(requestData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        if (data['result'] != null) {
          final List<dynamic> attendanceList = data['result'];

          try {
            return attendanceList
                .map((item) => Attendance.fromJson(item))
                .toList();
          } catch (parseError) {
            print('❌ Parse error: $parseError');
            throw Exception('Lỗi parse dữ liệu: $parseError');
          }
        } else if (data['error'] != null) {
          throw Exception(
            data['error']['message'] ??
                data['error']['data']['message'] ??
                'Lỗi không xác định',
          );
        }
      }

      throw Exception('Lỗi kết nối server: ${response.statusCode}');
    } catch (e) {
      throw Exception('Lỗi lấy dữ liệu lịch: $e');
    }
  }

  Future<Map<String, dynamic>> getCalendarData({int? month, int? year}) async {
    try {
      if (_apiService.sessionId == null) {
        throw Exception('Session không hợp lệ, vui lòng đăng nhập lại');
      }

      final params = <String, dynamic>{};
      if (month != null) params['month'] = month;
      if (year != null) params['year'] = year;

      final requestData = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": params,
      };

      final response = await http
          .post(
            Uri.parse('${AppConstants.baseUrl}/attendance/calendar'),
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'Cookie': 'session_id=${_apiService.sessionId}',
            },
            body: jsonEncode(requestData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['result'] != null) {
          return data['result'];
        } else if (data['error'] != null) {
          throw Exception(
            data['error']['message'] ??
                data['error']['data']['message'] ??
                'Lỗi không xác định',
          );
        }
      }

      throw Exception('Lỗi kết nối server: ${response.statusCode}');
    } catch (e) {
      throw Exception('Lỗi lấy dữ liệu calendar: $e');
    }
  }
}
