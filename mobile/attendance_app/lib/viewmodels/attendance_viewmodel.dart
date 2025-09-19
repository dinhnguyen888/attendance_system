import 'dart:io';
import 'package:flutter/foundation.dart';
import '../models/attendance.dart';
import '../services/attendance_service.dart';
import '../services/face_recognition_service.dart';

class AttendanceViewModel extends ChangeNotifier {
  final AttendanceService _attendanceService = AttendanceService();
  final FaceRecognitionService _faceService = FaceRecognitionService();

  AttendanceStatus? _status;
  bool _isLoading = false;
  String? _error;
  String? _successMessage;
  Map<String, dynamic>? _faceHealthStatus;

  AttendanceStatus? get status => _status;
  bool get isLoading => _isLoading;
  String? get error => _error;
  String? get successMessage => _successMessage;
  bool get faceServiceAvailable => _faceHealthStatus?['success'] == true;

  bool get canCheckIn => _status?.canCheckIn ?? false;
  bool get canCheckOut => _status?.canCheckOut ?? false;
  bool get needsFaceRegistration => _status?.needRegister ?? false;

  Future<void> initialize() async {
    await _checkFaceServiceHealth();
    await _loadStatus();
  }

  Future<void> _checkFaceServiceHealth() async {
    try {
      _faceHealthStatus = await _faceService.checkFaceHealth();
      if (_faceHealthStatus?['success'] != true) {
        _error = _faceHealthStatus?['error'] ??
            'Face recognition service unavailable';
      } else {
        _error = null;
      }
    } catch (e) {
      _faceHealthStatus = {'success': false, 'error': e.toString()};
      _error = 'Face recognition service unavailable: $e';
    }
    notifyListeners();
  }

  Future<void> _loadStatus() async {
    try {
      _setLoading(true);
      _error = null;

      final status = await _attendanceService.getStatus();
      _status = status;
    } catch (e) {
      _error = 'Failed to load status: $e';
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> performCheckIn(File faceImage, {String? wifiIp}) async {
    if (!faceServiceAvailable) {
      _error = 'Face recognition service is not available';
      notifyListeners();
      return false;
    }

    try {
      _setLoading(true);
      _clearMessages();

      final result = await _attendanceService.checkIn(
        faceImage: faceImage,
        wifiIp: wifiIp,
      );

      if (result['success'] == true) {
        _successMessage = result['message'] ?? 'Check-in thành công';
        await _loadStatus();
        return true;
      } else {
        _error = result['message'] ?? 'Check-in thất bại';
        return false;
      }
    } catch (e) {
      _error = 'Lỗi check-in: $e';
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> performCheckOut(File faceImage, {String? wifiIp}) async {
    if (!faceServiceAvailable) {
      _error = 'Face recognition service is not available';
      notifyListeners();
      return false;
    }

    try {
      _setLoading(true);
      _clearMessages();

      final result = await _attendanceService.checkOut(
        faceImage: faceImage,
        wifiIp: wifiIp,
      );

      if (result['success'] == true) {
        _successMessage = result['message'] ?? 'Check-out thành công';
        await _loadStatus();
        return true;
      } else {
        _error = result['message'] ?? 'Check-out thất bại';
        return false;
      }
    } catch (e) {
      _error = 'Lỗi check-out: $e';
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> registerFace(File faceImage) async {
    try {
      _setLoading(true);
      _clearMessages();

      final result = await _faceService.registerFace(
        faceImage: faceImage,
      );

      if (result['success'] == true) {
        _successMessage = result['message'] ?? 'Đăng ký khuôn mặt thành công';
        await _loadStatus();
        return true;
      } else {
        _error = result['message'] ?? 'Đăng ký khuôn mặt thất bại';
        return false;
      }
    } catch (e) {
      _error = 'Lỗi đăng ký khuôn mặt: $e';
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> refreshStatus() async {
    await _loadStatus();
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  void clearSuccess() {
    _successMessage = null;
    notifyListeners();
  }

  void _clearMessages() {
    _error = null;
    _successMessage = null;
  }

  String getStatusMessage() {
    if (_status == null) return 'Loading...';

    switch (_status!.status) {
      case 'checked_in':
        return 'Đã check-in lúc ${_status!.checkIn ?? "N/A"}';
      case 'checked_out':
        return 'Đã check-out lúc ${_status!.checkOut ?? "N/A"}';
      case 'no_face_registered':
        return 'Chưa đăng ký khuôn mặt. Vui lòng đăng ký trước khi chấm công.';
      default:
        return _status!.message;
    }
  }

  String getActionButtonText() {
    if (_status == null) return 'Loading...';

    switch (_status!.status) {
      case 'checked_in':
        return 'Check Out';
      case 'checked_out':
      case 'no_face_registered':
        return 'Check In';
      default:
        return 'Unknown';
    }
  }

  bool getActionButtonEnabled() {
    if (_status == null) return false;
    return faceServiceAvailable && (canCheckIn || canCheckOut);
  }

  String getFaceHealthStatusText() {
    if (_faceHealthStatus == null) return 'Đang kiểm tra...';
    if (_faceHealthStatus!['success'] == true) {
      final status = _faceHealthStatus!;
      return 'Face API: ${status['status'] ?? 'OK'} - OpenCV: ${status['opencv_version'] ?? 'N/A'}';
    }
    return 'Face API: Không khả dụng';
  }
}
