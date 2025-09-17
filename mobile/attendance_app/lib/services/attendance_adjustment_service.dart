import '../models/attendance_adjustment.dart';
import 'api_service.dart';

class AttendanceAdjustmentService {
  static final AttendanceAdjustmentService _instance =
      AttendanceAdjustmentService._internal();
  factory AttendanceAdjustmentService() => _instance;
  AttendanceAdjustmentService._internal();

  final ApiService _apiService = ApiService();

  Future<List<AttendanceAdjustment>> getAttendanceAdjustments({
    String? startDate,
    String? endDate,
  }) async {
    try {
      return await _apiService.getAttendanceAdjustments(
        startDate: startDate,
        endDate: endDate,
      );
    } catch (e) {
      throw Exception('Lỗi lấy danh sách yêu cầu chỉnh công: $e');
    }
  }

  Future<AttendanceAdjustment> createAttendanceAdjustment({
    required String date,
    String? originalCheckIn,
    String? originalCheckOut,
    String? requestedCheckIn,
    String? requestedCheckOut,
    required String reason,
  }) async {
    try {
      final request = AttendanceAdjustmentCreate(
        date: date,
        originalCheckIn: originalCheckIn,
        originalCheckOut: originalCheckOut,
        requestedCheckIn: requestedCheckIn,
        requestedCheckOut: requestedCheckOut,
        reason: reason,
      );

      return await _apiService.createAttendanceAdjustment(request);
    } catch (e) {
      throw Exception('Lỗi tạo yêu cầu chỉnh công: $e');
    }
  }

  Future<AttendanceAdjustment> getAttendanceAdjustment(int id) async {
    try {
      return await _apiService.getAttendanceAdjustment(id);
    } catch (e) {
      throw Exception('Lỗi lấy thông tin yêu cầu chỉnh công: $e');
    }
  }

  Future<Map<String, dynamic>> submitAttendanceAdjustment(int id) async {
    try {
      return await _apiService.submitAttendanceAdjustment(id);
    } catch (e) {
      throw Exception('Lỗi gửi yêu cầu chỉnh công: $e');
    }
  }

  Future<void> deleteAttendanceAdjustment(int id) async {
    try {
      await _apiService.deleteAttendanceAdjustment(id);
    } catch (e) {
      throw Exception('Lỗi hủy yêu cầu chỉnh công: $e');
    }
  }

  String getStateLabel(String state) {
    switch (state) {
      case 'draft':
        return 'Nháp';
      case 'submitted':
        return 'Đã gửi';
      case 'manager_approved':
        return 'QL đã duyệt';
      case 'hr_approved':
        return 'HR đã duyệt';
      case 'approved':
        return 'Đã duyệt';
      case 'rejected':
        return 'Từ chối';
      default:
        return state;
    }
  }
}
