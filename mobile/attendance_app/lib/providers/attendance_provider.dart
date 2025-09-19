import 'dart:io';
import 'package:flutter/foundation.dart';
import '../services/attendance_service.dart';
import '../services/face_recognition_service.dart';
import '../services/calendar_service.dart';
import '../services/api_service.dart';
import '../models/attendance.dart';

class AttendanceProvider extends ChangeNotifier {
  final AttendanceService _attendanceService = AttendanceService();
  final FaceRecognitionService _faceService = FaceRecognitionService();
  final CalendarService _calendarService = CalendarService();
  final ApiService _apiService = ApiService();

  AttendanceStatus? _currentStatus;
  bool _isLoading = false;
  String? _errorMessage;
  String? _calendarError;
  bool _faceHealthOk = false;
  List<Attendance> _attendanceHistory = [];
  Map<String, dynamic> _attendanceCalendar = {};
  String? _successMessage;

  AttendanceStatus? get currentStatus => _currentStatus;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String? get calendarError => _calendarError;
  bool get faceHealthOk => _faceHealthOk;
  List<Attendance> get attendanceHistory => _attendanceHistory;
  Map<String, dynamic> get attendanceCalendar => _attendanceCalendar;
  String? get successMessage => _successMessage;

  bool get canCheckIn {
    if (_currentStatus == null) return false;
    return _currentStatus!.canCheckIn;
  }

  bool get canCheckOut {
    if (_currentStatus == null) return false;
    return _currentStatus!.canCheckOut;
  }

  bool get needsFaceRegistration {
    if (_currentStatus == null) return false;
    return _currentStatus!.needRegister;
  }

  String? get error => _errorMessage;

  Future<void> initialize() async {
    try {
      _setLoading(true);
      _errorMessage = null;

      if (_apiService.sessionId == null) {
        _errorMessage = 'Chưa đăng nhập, vui lòng đăng nhập trước';
        return;
      }

      await checkFaceHealth();
      await refreshStatus();
    } catch (e) {
      _errorMessage = 'Lỗi khởi tạo: $e';
    } finally {
      _setLoading(false);
    }
  }

  Future<void> checkFaceHealth() async {
    try {
      _setLoading(true);
      final health = await _faceService.checkFaceHealth();
      _faceHealthOk = health['success'] == true;
      _errorMessage = null;
    } catch (e) {
      _faceHealthOk = false;
      _errorMessage = 'Face recognition service unavailable';
    } finally {
      _setLoading(false);
    }
  }

  Future<void> refreshStatus() async {
    try {
      _setLoading(true);
      _errorMessage = null;

      final status = await _attendanceService.getStatus();
      _currentStatus = status;
    } catch (e) {
      _errorMessage = 'Failed to get status: $e';
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> checkIn(File faceImage, {String? wifiIp}) async {
    try {
      _setLoading(true);
      _errorMessage = null;
      _successMessage = null;

      if (!_faceHealthOk) {
        _errorMessage = 'Face recognition service is not available';
        return false;
      }

      final result = await _attendanceService.checkIn(
        faceImage: faceImage,
        wifiIp: wifiIp,
      );

      if (result['success'] == true) {
        await refreshStatus();
        _setSuccessMessage(
          result['message'] ?? 'Check-in thành công với xác thực khuôn mặt!',
        );
        return true;
      } else {
        _errorMessage = result['message'] ?? 'Check-in thất bại';
        return false;
      }
    } catch (e) {
      _errorMessage = 'Lỗi check-in: $e';
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> checkOut(File faceImage, {String? wifiIp}) async {
    try {
      _setLoading(true);
      _errorMessage = null;
      _successMessage = null;

      if (!_faceHealthOk) {
        _errorMessage = 'Face recognition service is not available';
        return false;
      }

      final result = await _attendanceService.checkOut(
        faceImage: faceImage,
        wifiIp: wifiIp,
      );

      if (result['success'] == true) {
        await refreshStatus();
        _setSuccessMessage(
          result['message'] ?? 'Check-out thành công với xác thực khuôn mặt!',
        );
        return true;
      } else {
        _errorMessage = result['message'] ?? 'Check-out thất bại';
        return false;
      }
    } catch (e) {
      _errorMessage = 'Lỗi check-out: $e';
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> checkAttendance({
    required String action,
    required File faceImage,
    String? wifiIp,
  }) async {
    if (action == 'check_in') {
      return await checkIn(faceImage, wifiIp: wifiIp);
    } else if (action == 'check_out') {
      return await checkOut(faceImage, wifiIp: wifiIp);
    }
    return false;
  }

  Future<bool> registerFace(File faceImage) async {
    try {
      _setLoading(true);
      _errorMessage = null;
      _successMessage = null;

      final result = await _faceService.registerFace(faceImage: faceImage);

      if (result['success'] == true) {
        await refreshStatus();
        _setSuccessMessage(
          result['message'] ?? 'Đăng ký khuôn mặt thành công!',
        );
        return true;
      } else {
        _errorMessage = result['message'] ?? 'Đăng ký khuôn mặt thất bại';
        return false;
      }
    } catch (e) {
      _errorMessage = 'Lỗi đăng ký khuôn mặt: $e';
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> loadAttendanceStatus() async {
    await refreshStatus();
  }

  Future<void> loadAttendanceHistory({
    String? startDate,
    String? endDate,
  }) async {
    try {
      _setLoading(true);
      _errorMessage = null;

      _attendanceHistory = [
        Attendance(
          id: 1,
          employeeId: 1,
          checkIn:
              DateTime.now().subtract(Duration(hours: 8)).toIso8601String(),
          checkOut: DateTime.now().toIso8601String(),
          date: DateTime.now().toIso8601String().split('T')[0],
          status: 'completed',
          totalHours: 8.0,
        ),
      ];
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Failed to load attendance history: $e';
    } finally {
      _setLoading(false);
    }
  }

  Future<void> loadInitialData() async {
    try {
      _calendarError = null;

      // Kiểm tra session trước khi load data
      if (_apiService.sessionId == null) {
        _calendarError = 'Session không hợp lệ, vui lòng đăng nhập lại';
        return;
      }

      // Lấy TẤT CẢ dữ liệu thực tế từ Odoo API
      try {
        _attendanceHistory = await _calendarService.getAttendanceHistory();

        // Calendar data với dữ liệu thực tế từ API
        _attendanceCalendar = {
          'attendances': _attendanceHistory.map((a) => a.toJson()).toList(),
        };

        // Debug log
      } catch (apiError) {
        _calendarError = 'Không thể lấy dữ liệu từ server: $apiError';
        _attendanceHistory = [];
        _attendanceCalendar = {'attendances': []};
      }
    } catch (e) {
      _calendarError = 'Failed to load initial data: $e';
    }
  }

  Future<void> loadAttendanceCalendar({int? month, int? year}) async {
    try {
      _setLoading(true);
      _calendarError = null;

      if (_apiService.sessionId == null) {
        _calendarError = 'Session không hợp lệ, vui lòng đăng nhập lại';
        return;
      }

      // Lấy dữ liệu cho tháng cụ thể
      final targetYear = year ?? DateTime.now().year;
      final targetMonth = month ?? DateTime.now().month;

      final startDate = DateTime(targetYear, targetMonth, 1).toIso8601String();
      final endDate = DateTime(
        targetYear,
        targetMonth + 1,
        0,
        23,
        59,
        59,
      ).toIso8601String();

      try {
        final monthlyData = await _calendarService.getAttendanceHistory(
          startDate: startDate,
          endDate: endDate,
        );

        // Cập nhật cả history và calendar data
        _attendanceHistory = monthlyData;
        _attendanceCalendar = {
          'attendances': _attendanceHistory.map((a) => a.toJson()).toList(),
        };

        print(
          '📅 Loaded ${monthlyData.length} records for $targetMonth/$targetYear',
        );
      } catch (apiError) {
        _calendarError =
            'Không thể lấy dữ liệu tháng $targetMonth/$targetYear: $apiError';
      }
    } catch (e) {
      _calendarError = 'Failed to load calendar for month: $e';
    } finally {
      _setLoading(false);
    }
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setSuccessMessage(String message) {
    _successMessage = message;
    _errorMessage = null;
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    _successMessage = null;
    notifyListeners();
  }

  void clearCalendarError() {
    _calendarError = null;
    notifyListeners();
  }

  void clearHistory() {
    _attendanceHistory.clear();
    notifyListeners();
  }
}
