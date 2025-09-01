import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../constants/app_constants.dart';
import '../models/auth.dart';
import '../models/employee.dart';
import '../models/attendance.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _token;
  String? _sessionId;

  void setToken(String token) {
    _token = token;
  }

  void setSessionId(String sessionId) {
    _sessionId = sessionId;
  }

  String? get token => _token;
  String? get sessionId => _sessionId;

  Map<String, String> get _headers {
    final headers = <String, String>{
      'Content-Type': 'application/json',
    };
    if (_sessionId != null) {
      headers['Cookie'] = 'session_id=$_sessionId';
    }
    return headers;
  }

  Future<LoginResponse> login(String username, String password) async {
    try {
      final odooLoginUrl = '${AppConstants.baseUrl}/web/session/authenticate';
      final odooLoginData = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {"db": "odoo_db", "login": username, "password": password}
      };

      final odooResponse = await http
          .post(
            Uri.parse(odooLoginUrl),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(odooLoginData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (odooResponse.statusCode == 200) {
        final odooData = jsonDecode(odooResponse.body);

        if (odooData['result'] != null && odooData['result']['uid'] != null) {
          final cookies = odooResponse.headers['set-cookie'];
          if (cookies != null) {
            final sessionMatch =
                RegExp(r'session_id=([^;]+)').firstMatch(cookies);
            if (sessionMatch != null) {
              final sessionId = sessionMatch.group(1);
              setSessionId(sessionId!);
            }
          }
        }
      }

      final url = '${AppConstants.baseUrl}/mobile/auth/login';
      final requestData = {"username": username, "password": password};

      final response = await http
          .post(
            Uri.parse(url),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(requestData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        if (data['success'] == true && data['employee'] != null) {
          _token = data['token'];

          final employee = Employee(
            id: data['employee']['id'] ?? 0,
            name: data['employee']['name'] ?? '',
            employeeCode: data['employee']['employee_code'] ?? '',
            department: data['employee']['department'] ?? '',
            position: data['employee']['position'] ?? '',
            email: data['employee']['email'] ?? '',
            phone: data['employee']['phone'] ?? '',
            faceRegistered: data['employee']['face_registered'] ?? false,
          );

          return LoginResponse(
            success: true,
            message: data['message'] ?? 'Đăng nhập thành công',
            token: data['token'],
            employee: employee,
          );
        } else {
          final errorMsg = data['message'] ?? 'Đăng nhập thất bại';
          return LoginResponse(
            success: false,
            message: errorMsg,
          );
        }
      } else {
        String errorMessage;
        switch (response.statusCode) {
          case 401:
            errorMessage = 'Tên đăng nhập hoặc mật khẩu không đúng';
            break;
          case 500:
            errorMessage = 'Lỗi server, vui lòng thử lại sau';
            break;
          default:
            errorMessage = 'Đăng nhập thất bại (${response.statusCode})';
        }
        return LoginResponse(
          success: false,
          message: errorMessage,
        );
      }
    } catch (e) {
      return LoginResponse(
        success: false,
        message: 'Lỗi kết nối: $e',
      );
    }
  }

  Future<Employee> getProfile() async {
    try {
      final detailedProfile = await getCurrentUserProfile();
      if (detailedProfile != null) {
        return detailedProfile;
      }

      return Employee(
        id: 0,
        name: 'Chưa có',
        employeeCode: 'Chưa có',
        department: 'Chưa có',
        position: 'Chưa có',
        email: 'Chưa có',
        phone: 'Chưa có',
        faceRegistered: false,
      );
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<List<Attendance>> getAttendanceHistory({
    String? startDate,
    String? endDate,
  }) async {
    try {
      if (_token == null) {
        throw Exception('Token không hợp lệ');
      }

      final queryParams = <String, String>{};
      if (startDate != null) queryParams['start_date'] = startDate;
      if (endDate != null) queryParams['end_date'] = endDate;

      final uri = Uri.parse('${AppConstants.baseUrl}/mobile/attendance/history')
          .replace(queryParameters: queryParams);

      final response = await http.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_token',
        },
      ).timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data is List) {
          return data.map((json) => Attendance.fromJson(json)).toList();
        }
      }
      throw Exception(
          'Failed to get attendance history: ${response.statusCode}');
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> getAttendanceCalendar({
    int? month,
    int? year,
  }) async {
    try {
      if (_token == null) {
        throw Exception('Token không hợp lệ');
      }

      final queryParams = <String, String>{};
      if (month != null) queryParams['month'] = month.toString();
      if (year != null) queryParams['year'] = year.toString();

      final uri =
          Uri.parse('${AppConstants.baseUrl}/mobile/attendance/calendar')
              .replace(queryParameters: queryParams);

      final response = await http.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_token',
        },
      ).timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data;
      }
      throw Exception(
          'Failed to get attendance calendar: ${response.statusCode}');
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<bool> checkAttendance({
    required int employeeId,
    required String action,
    File? faceImage,
    double? latitude,
    double? longitude,
    String? wifiName,
    bool? validWifi,
    String? deviceInfo,
  }) async {
    try {
      if (_sessionId == null) {
        throw Exception('Session không hợp lệ');
      }

      final endpoint = action == 'check_in'
          ? '/attendance/check_in'
          : '/attendance/check_out';

      final attendanceData = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
          "face_image":
              faceImage != null ? await _fileToBase64(faceImage) : null,
          "wifi_ip": wifiName,
        }
      };

      final response = await http
          .post(
            Uri.parse('${AppConstants.baseUrl}$endpoint'),
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'Cookie': 'session_id=$_sessionId',
            },
            body: jsonEncode(attendanceData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        if (data['result'] != null) {
          return true;
        } else if (data['error'] != null) {
          throw Exception(
              'Odoo API error: ${data['error']['data']['message'] ?? data['error']['message']}');
        }
      }

      throw Exception(
          'Không thể tạo bản ghi chấm công - Status: ${response.statusCode}');
    } catch (e) {
      return false;
    }
  }

  Future<String> _fileToBase64(File file) async {
    final bytes = await file.readAsBytes();
    return base64Encode(bytes);
  }

  Future<AttendanceStatus> getAttendanceStatus() async {
    try {
      if (_sessionId == null) {
        throw Exception('Session không hợp lệ');
      }

      final statusData = {"jsonrpc": "2.0", "method": "call", "params": {}};

      final response = await http
          .post(
            Uri.parse('${AppConstants.baseUrl}/attendance/status'),
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'Cookie': 'session_id=$_sessionId',
            },
            body: jsonEncode(statusData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        if (data['result'] != null) {
          final result = data['result'];
          return AttendanceStatus(
            status: result['status'] ?? '',
            message: result['message'] ?? '',
            checkIn: result['check_in_time'],
            checkOut: result['check_out_time'],
            totalHours: 0.0,
          );
        } else {
          throw Exception(data['error'] ?? 'Unknown error');
        }
      }
      throw Exception(
          'Failed to get attendance status: ${response.statusCode}');
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> getAttendanceStatistics({
    int? month,
    int? year,
  }) async {
    try {
      if (_sessionId == null) {
        throw Exception('Session không hợp lệ');
      }

      final domain = [
        ["employee_id", "=", 0]
      ];

      if (month != null && year != null) {
        domain.add(
            ["check_in", ">=", DateTime(year, month, 1).toIso8601String()]);
        domain.add(
            ["check_in", "<", DateTime(year, month + 1, 1).toIso8601String()]);
      }

      final requestData = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
          "model": "hr.attendance",
          "method": "read_group",
          "args": [],
          "kwargs": {
            "domain": domain,
            "fields": ["worked_hours:sum"],
            "groupby": ["employee_id"],
            "context": {"lang": "vi_VN", "tz": "Asia/Ho_Chi_Minh"}
          }
        }
      };

      final response = await http
          .post(
            Uri.parse(
                '${AppConstants.baseUrl}${AppConstants.apiVersion}/dataset/call_kw'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(requestData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['result'] != null && data['result'].isNotEmpty) {
          final result = data['result'][0];
          return {
            'totalHours': result['worked_hours'] ?? 0.0,
            'daysWorked': result['__count'] ?? 0,
          };
        }
      }

      return {'totalHours': 0.0, 'daysWorked': 0};
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Employee?> getCurrentUserProfile() async {
    try {
      if (_token == null) {
        throw Exception('Token không hợp lệ');
      }

      final response = await http.get(
        Uri.parse('${AppConstants.baseUrl}/mobile/employee/profile'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_token',
        },
      ).timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        return Employee(
          id: data['employee_id'] ?? 0,
          name: data['name'] ?? '',
          employeeCode: data['employee_code'] ?? '',
          department: data['department'] ?? '',
          position: data['position'] ?? '',
          email: data['email'] ?? '',
          phone: data['phone'] ?? '',
          faceRegistered: data['face_registered'] ?? false,
        );
      }
      throw Exception('Failed to get profile: ${response.statusCode}');
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<void> refreshSession() async {
    try {
      if (_token == null) {
        throw Exception('Token không hợp lệ');
      }

      final response = await http.get(
        Uri.parse('${AppConstants.baseUrl}/mobile/employee/profile'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_token',
        },
      ).timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        // Session refreshed successfully
      } else {
        throw Exception('Session hết hạn, vui lòng đăng nhập lại');
      }
    } catch (e) {
      throw Exception('Lỗi refresh session: $e');
    }
  }

  bool get isSessionValid => _token != null;

  String _safeString(dynamic value) {
    if (value == null || value == false) {
      return 'Chưa có';
    }
    return value.toString();
  }
}
