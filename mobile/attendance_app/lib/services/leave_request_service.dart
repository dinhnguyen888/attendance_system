import '../models/leave_request.dart';
import 'api_service.dart';

class LeaveRequestService {
  static final LeaveRequestService _instance = LeaveRequestService._internal();
  factory LeaveRequestService() => _instance;
  LeaveRequestService._internal();

  final ApiService _apiService = ApiService();

  Future<List<LeaveRequest>> getLeaveRequests({
    String? startDate,
    String? endDate,
  }) async {
    try {
      return await _apiService.getLeaveRequests(
        startDate: startDate,
        endDate: endDate,
      );
    } catch (e) {
      throw Exception('Lỗi lấy danh sách đơn nghỉ phép: $e');
    }
  }

  Future<LeaveRequest> createLeaveRequest({
    required String leaveType,
    required String startDate,
    required String endDate,
    required String reason,
  }) async {
    try {
      final request = LeaveRequestCreate(
        leaveType: leaveType,
        startDate: startDate,
        endDate: endDate,
        reason: reason,
      );

      return await _apiService.createLeaveRequest(request);
    } catch (e) {
      throw Exception('Lỗi tạo đơn nghỉ phép: $e');
    }
  }

  Future<LeaveRequest> getLeaveRequest(int id) async {
    try {
      return await _apiService.getLeaveRequest(id);
    } catch (e) {
      throw Exception('Lỗi lấy thông tin đơn nghỉ phép: $e');
    }
  }

  Future<Map<String, dynamic>> submitLeaveRequest(int id) async {
    try {
      return await _apiService.submitLeaveRequest(id);
    } catch (e) {
      throw Exception('Lỗi gửi đơn nghỉ phép: $e');
    }
  }

  Future<void> deleteLeaveRequest(int id) async {
    try {
      await _apiService.deleteLeaveRequest(id);
    } catch (e) {
      throw Exception('Lỗi hủy đơn nghỉ phép: $e');
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

  String getLeaveTypeLabel(String leaveType) {
    final types = LeaveType.getLeaveTypes();
    final type = types.firstWhere(
      (t) => t.value == leaveType,
      orElse: () => LeaveType(value: leaveType, label: leaveType),
    );
    return type.label;
  }
}
