import 'package:flutter/foundation.dart';
import 'dart:io';
import '../models/attendance.dart';
import '../services/api_service.dart';

class AttendanceProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();

  bool _isLoading = false;
  String? _error;
  List<Attendance> _attendanceHistory = [];
  Map<String, dynamic> _attendanceCalendar = {};
  AttendanceStatus? _currentStatus;
  Map<String, dynamic>? _statistics;

  bool get isLoading => _isLoading;
  String? get error => _error;
  List<Attendance> get attendanceHistory => _attendanceHistory;
  Map<String, dynamic> get attendanceCalendar => _attendanceCalendar;
  AttendanceStatus? get currentStatus => _currentStatus;
  Map<String, dynamic>? get statistics => _statistics;

  Future<void> loadAttendanceHistory(
      {String? startDate, String? endDate}) async {
    try {
      _setLoading(true);
      _clearError();

      final history = await _apiService.getAttendanceHistory(
        startDate: startDate,
        endDate: endDate,
      );

      _attendanceHistory = history;
      notifyListeners();
    } catch (e) {
      _setError(e.toString());
    } finally {
      _setLoading(false);
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
      _setLoading(true);
      _clearError();

      final result = await _apiService.checkAttendance(
        employeeId: employeeId,
        action: action,
        faceImage: faceImage,
        latitude: latitude,
        longitude: longitude,
        wifiName: wifiName,
        validWifi: validWifi,
        deviceInfo: deviceInfo,
      );

      if (result) {
        await loadAttendanceStatus();
        await loadAttendanceHistory();
        await loadAttendanceCalendar();
        return true;
      } else {
        _setError('Chấm công thất bại');
        return false;
      }
    } catch (e) {
      _setError(e.toString());
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> loadAttendanceStatus() async {
    try {
      _clearError();

      final status = await _apiService.getAttendanceStatus();
      _currentStatus = status;
      notifyListeners();
    } catch (e) {
      _setError(e.toString());
    }
  }

  Future<void> loadStatistics({int? month, int? year}) async {
    try {
      _setLoading(true);
      _clearError();

      final stats = await _apiService.getAttendanceStatistics(
        month: month,
        year: year,
      );

      if (stats['success'] == true) {
        _statistics = stats;
        notifyListeners();
      } else {
        _setError(stats['message'] ?? 'Không thể tải thống kê');
      }
    } catch (e) {
      _setError(e.toString());
    } finally {
      _setLoading(false);
    }
  }

  Future<void> loadAttendanceCalendar({int? month, int? year}) async {
    try {
      _setLoading(true);
      _clearError();

      final calendar = await _apiService.getAttendanceCalendar(
        month: month,
        year: year,
      );

      _attendanceCalendar = calendar;
      notifyListeners();
    } catch (e) {
      _setError(e.toString());
    } finally {
      _setLoading(false);
    }
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String error) {
    _error = error;
    notifyListeners();
  }

  void _clearError() {
    _error = null;
    notifyListeners();
  }

  void clearError() {
    _clearError();
  }

  void clearHistory() {
    _attendanceHistory.clear();
    notifyListeners();
  }
}
