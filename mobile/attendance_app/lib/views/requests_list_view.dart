import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../models/leave_request.dart';
import '../models/attendance_adjustment.dart';
import '../services/leave_request_service.dart';
import '../services/attendance_adjustment_service.dart';
import '../widgets/custom_button.dart';

class RequestsListView extends StatefulWidget {
  const RequestsListView({super.key});

  @override
  State<RequestsListView> createState() => _RequestsListViewState();
}

class _RequestsListViewState extends State<RequestsListView>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _leaveService = LeaveRequestService();
  final _adjustmentService = AttendanceAdjustmentService();

  List<LeaveRequest> _leaveRequests = [];
  List<AttendanceAdjustment> _adjustments = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);

    try {
      final results = await Future.wait([
        _leaveService.getLeaveRequests(),
        _adjustmentService.getAttendanceAdjustments(),
      ]);

      setState(() {
        _leaveRequests = results[0] as List<LeaveRequest>;
        _adjustments = results[1] as List<AttendanceAdjustment>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      _showSnackBar('Lỗi tải dữ liệu: $e', AppColors.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: _buildAppBar(),
      body: Column(
        children: [
          _buildTabBar(),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildLeaveRequestsTab(),
                _buildAdjustmentsTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text(
        'Danh sách yêu cầu',
        style: TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: 18,
        ),
      ),
      backgroundColor: AppColors.primary,
      elevation: 0,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back, color: Colors.white),
        onPressed: () => Navigator.pop(context),
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh, color: Colors.white),
          onPressed: _loadData,
        ),
      ],
    );
  }

  Widget _buildTabBar() {
    return Container(
      color: AppColors.primary,
      child: TabBar(
        controller: _tabController,
        indicatorColor: Colors.white,
        indicatorWeight: 3,
        labelColor: Colors.white,
        unselectedLabelColor: Colors.white70,
        labelStyle: const TextStyle(fontWeight: FontWeight.bold),
        tabs: const [
          Tab(
            icon: Icon(Icons.event_available, size: 20),
            text: 'Đơn nghỉ phép',
          ),
          Tab(
            icon: Icon(Icons.edit_calendar, size: 20),
            text: 'Yêu cầu chỉnh công',
          ),
        ],
      ),
    );
  }

  Widget _buildLeaveRequestsTab() {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.primary),
      );
    }

    if (_leaveRequests.isEmpty) {
      return _buildEmptyState(
        icon: Icons.event_available,
        title: 'Chưa có đơn nghỉ phép',
        subtitle: 'Bạn chưa tạo đơn nghỉ phép nào',
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      color: AppColors.primary,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _leaveRequests.length,
        itemBuilder: (context, index) {
          final request = _leaveRequests[index];
          return _buildLeaveRequestCard(request);
        },
      ),
    );
  }

  Widget _buildAdjustmentsTab() {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.primary),
      );
    }

    if (_adjustments.isEmpty) {
      return _buildEmptyState(
        icon: Icons.edit_calendar,
        title: 'Chưa có yêu cầu chỉnh công',
        subtitle: 'Bạn chưa tạo yêu cầu chỉnh công nào',
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      color: AppColors.primary,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _adjustments.length,
        itemBuilder: (context, index) {
          final adjustment = _adjustments[index];
          return _buildAdjustmentCard(adjustment);
        },
      ),
    );
  }

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 64, color: AppColors.textHint),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            subtitle,
            style: const TextStyle(
              fontSize: 14,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLeaveRequestCard(LeaveRequest request) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.event_available,
                  color: _getStateColor(request.state),
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    request.name,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
                _buildStateChip(request.state),
              ],
            ),
            const SizedBox(height: 12),
            _buildInfoRow('Loại nghỉ',
                _leaveService.getLeaveTypeLabel(request.leaveType)),
            _buildInfoRow('Từ ngày', request.startDate),
            _buildInfoRow('Đến ngày', request.endDate),
            _buildInfoRow('Số ngày', '${request.daysRequested.toInt()} ngày'),
            if (request.reason.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                'Lý do: ${request.reason}',
                style: const TextStyle(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            if (request.rejectionReason != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.error.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: AppColors.error.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    Icon(Icons.cancel, color: AppColors.error, size: 16),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Lý do từ chối: ${request.rejectionReason}',
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.error,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            if (request.state == 'draft') ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: CustomButton(
                      onPressed: () => _submitLeaveRequest(request.id),
                      text: 'Gửi đơn',
                      backgroundColor: AppColors.primary,
                      icon: Icons.send,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: CustomButton(
                      onPressed: () => _deleteLeaveRequest(request.id),
                      text: 'Hủy',
                      backgroundColor: AppColors.error,
                      icon: Icons.delete,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildAdjustmentCard(AttendanceAdjustment adjustment) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.edit_calendar,
                  color: _getStateColor(adjustment.state),
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    adjustment.name,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
                _buildStateChip(adjustment.state),
              ],
            ),
            const SizedBox(height: 12),
            _buildInfoRow('Ngày', adjustment.date),
            if (adjustment.originalCheckIn != null)
              _buildInfoRow('Check In hiện tại', adjustment.originalCheckIn!),
            if (adjustment.originalCheckOut != null)
              _buildInfoRow('Check Out hiện tại', adjustment.originalCheckOut!),
            if (adjustment.requestedCheckIn != null)
              _buildInfoRow('Check In yêu cầu', adjustment.requestedCheckIn!),
            if (adjustment.requestedCheckOut != null)
              _buildInfoRow('Check Out yêu cầu', adjustment.requestedCheckOut!),
            if (adjustment.reason.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                'Lý do: ${adjustment.reason}',
                style: const TextStyle(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            if (adjustment.rejectionReason != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.error.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: AppColors.error.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    Icon(Icons.cancel, color: AppColors.error, size: 16),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Lý do từ chối: ${adjustment.rejectionReason}',
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.error,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            if (adjustment.state == 'draft') ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: CustomButton(
                      onPressed: () =>
                          _submitAttendanceAdjustment(adjustment.id),
                      text: 'Gửi yêu cầu',
                      backgroundColor: AppColors.primary,
                      icon: Icons.send,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: CustomButton(
                      onPressed: () =>
                          _deleteAttendanceAdjustment(adjustment.id),
                      text: 'Hủy',
                      backgroundColor: AppColors.error,
                      icon: Icons.delete,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(
              '$label:',
              style: const TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 14,
                color: AppColors.textPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStateChip(String state) {
    Color color;
    String label;

    switch (state) {
      case 'draft':
        color = AppColors.textHint;
        label = 'Nháp';
        break;
      case 'submitted':
        color = AppColors.info;
        label = 'Chờ duyệt';
        break;
      case 'manager_approved':
        color = AppColors.warning;
        label = 'QL đã duyệt';
        break;
      case 'hr_approved':
        color = AppColors.warning;
        label = 'HR đã duyệt';
        break;
      case 'approved':
        color = AppColors.success;
        label = 'Đã duyệt';
        break;
      case 'rejected':
        color = AppColors.error;
        label = 'Từ chối';
        break;
      default:
        color = AppColors.textHint;
        label = state;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.bold,
          color: color,
        ),
      ),
    );
  }

  Color _getStateColor(String state) {
    switch (state) {
      case 'draft':
        return AppColors.textHint;
      case 'submitted':
        return AppColors.info;
      case 'manager_approved':
        return AppColors.warning;
      case 'hr_approved':
        return AppColors.warning;
      case 'approved':
        return AppColors.success;
      case 'rejected':
        return AppColors.error;
      default:
        return AppColors.textHint;
    }
  }

  Future<void> _submitLeaveRequest(int id) async {
    try {
      final result = await _leaveService.submitLeaveRequest(id);

      if (mounted) {
        _showSnackBar(
            result['message'] ?? 'Đơn nghỉ phép đã được gửi thành công!',
            AppColors.success);
        _loadData(); // Reload data to update state
      }
    } catch (e) {
      if (mounted) {
        _showSnackBar('Lỗi gửi đơn nghỉ phép: $e', AppColors.error);
      }
    }
  }

  Future<void> _submitAttendanceAdjustment(int id) async {
    try {
      final result = await _adjustmentService.submitAttendanceAdjustment(id);

      if (mounted) {
        _showSnackBar(
            result['message'] ?? 'Yêu cầu chỉnh công đã được gửi thành công!',
            AppColors.success);
        _loadData();
      }
    } catch (e) {
      if (mounted) {
        _showSnackBar('Lỗi gửi yêu cầu chỉnh công: $e', AppColors.error);
      }
    }
  }

  Future<void> _deleteLeaveRequest(int id) async {
    final confirmed = await _showConfirmDialog(
      'Xác nhận hủy',
      'Bạn có chắc chắn muốn hủy đơn nghỉ phép này?',
    );

    if (!confirmed) return;

    try {
      await _leaveService.deleteLeaveRequest(id);
      if (mounted) {
        _showSnackBar('Đơn nghỉ phép đã được hủy', AppColors.success);
        _loadData();
      }
    } catch (e) {
      if (mounted) {
        _showSnackBar('Lỗi hủy đơn nghỉ phép: $e', AppColors.error);
      }
    }
  }

  Future<void> _deleteAttendanceAdjustment(int id) async {
    final confirmed = await _showConfirmDialog(
      'Xác nhận hủy',
      'Bạn có chắc chắn muốn hủy yêu cầu chỉnh công này?',
    );

    if (!confirmed) return;

    try {
      await _adjustmentService.deleteAttendanceAdjustment(id);
      if (mounted) {
        _showSnackBar('Yêu cầu chỉnh công đã được hủy', AppColors.success);
        _loadData();
      }
    } catch (e) {
      if (mounted) {
        _showSnackBar('Lỗi hủy yêu cầu chỉnh công: $e', AppColors.error);
      }
    }
  }

  Future<bool> _showConfirmDialog(String title, String message) async {
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text(title),
            content: Text(message),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: const Text('Hủy'),
              ),
              TextButton(
                onPressed: () => Navigator.of(context).pop(true),
                child: const Text('Xác nhận'),
              ),
            ],
          ),
        ) ??
        false;
  }

  void _showSnackBar(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              color == AppColors.success ? Icons.check_circle : Icons.error,
              color: Colors.white,
              size: 20,
            ),
            const SizedBox(width: 8),
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: color,
        duration: const Duration(seconds: 3),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );
  }
}
