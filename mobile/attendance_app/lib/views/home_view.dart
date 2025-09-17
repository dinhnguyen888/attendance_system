import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/attendance_provider.dart';
import '../constants/app_colors.dart';

import '../widgets/attendance_card.dart';
import '../widgets/profile_card.dart';
import '../widgets/attendance_calendar.dart';
import '../services/wifi_service.dart';
import 'camera_view.dart';
import 'leave_request_view.dart';
import 'attendance_adjustment_view.dart';
import 'requests_list_view.dart';
import '../widgets/error_dialog.dart';

class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  final WiFiService _wifiService = WiFiService();
  DateTime? _lastRefreshTime;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeData();
    });
  }

  Future<void> _initializeData() async {
    final attendanceProvider = context.read<AttendanceProvider>();
    final authProvider = context.read<AuthProvider>();

    try {
      await attendanceProvider.initialize();
      await authProvider.refreshUserProfile();
      _lastRefreshTime = DateTime.now();
    } catch (e) {
      print('Error initializing data: $e');
    }
  }

  Future<void> _refreshData() async {
    final attendanceProvider = context.read<AttendanceProvider>();
    final authProvider = context.read<AuthProvider>();

    try {
      await Future.wait([
        attendanceProvider.refreshStatus(),
        attendanceProvider.loadInitialData(),
        authProvider.refreshUserProfile(),
      ]);

      _lastRefreshTime = DateTime.now();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Row(
              children: [
                Icon(Icons.refresh, color: Colors.white),
                SizedBox(width: 8),
                Text('Dữ liệu đã được cập nhật'),
              ],
            ),
            backgroundColor: AppColors.success,
            duration: const Duration(seconds: 2),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.error, color: Colors.white),
                const SizedBox(width: 8),
                Expanded(
                    child: Text(
                        'Lỗi cập nhật: ${e.toString().length > 50 ? e.toString().substring(0, 50) + '...' : e.toString()}')),
              ],
            ),
            backgroundColor: AppColors.error,
            duration: const Duration(seconds: 3),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            action: SnackBarAction(
              label: 'Thử lại',
              textColor: Colors.white,
              onPressed: _refreshData,
            ),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: _buildAppBar(),
      body: RefreshIndicator(
        onRefresh: _refreshData,
        color: AppColors.primary,
        backgroundColor: Colors.white,
        strokeWidth: 2.5,
        displacement: 40.0,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const ProfileCard(),
              const SizedBox(height: 24),
              const AttendanceCard(),
              const SizedBox(height: 24),
              _buildQuickActions(),
              const SizedBox(height: 24),
              _buildRequestActions(),
              const SizedBox(height: 24),
              const AttendanceCalendar(),
            ],
          ),
        ),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Attendance System',
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 18,
            ),
          ),
          if (_lastRefreshTime != null)
            Text(
              'Cập nhật: ${_formatTime(_lastRefreshTime!)}',
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 12,
              ),
            ),
        ],
      ),
      backgroundColor: AppColors.primary,
      elevation: 0,
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh, color: Colors.white),
          onPressed: _refreshData,
          tooltip: 'Cập nhật dữ liệu',
        ),
        IconButton(
          icon: const Icon(Icons.logout, color: Colors.white),
          onPressed: () => _showLogoutDialog(),
        ),
      ],
    );
  }

  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final diff = now.difference(time);

    if (diff.inMinutes < 1) {
      return 'vừa xong';
    } else if (diff.inMinutes < 60) {
      return '${diff.inMinutes} phút trước';
    } else if (diff.inHours < 24) {
      return '${diff.inHours} giờ trước';
    } else {
      return '${time.day}/${time.month} ${time.hour}:${time.minute.toString().padLeft(2, '0')}';
    }
  }

  Widget _buildQuickActions() {
    return Consumer<AttendanceProvider>(
      builder: (context, provider, child) {
        return Card(
          elevation: 2,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.face_retouching_natural,
                      color: AppColors.primary,
                      size: 24,
                    ),
                    const SizedBox(width: 8),
                    const Text(
                      'Chấm Công',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: (provider.canCheckIn && !provider.isLoading)
                            ? () => _checkAttendance('check_in')
                            : null,
                        icon: provider.isLoading
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  color: Colors.white,
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(Icons.login),
                        label: Text(
                            provider.isLoading ? 'Đang xử lý...' : 'Check In'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: provider.canCheckIn
                              ? AppColors.checkIn
                              : Colors.grey.shade400,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: (provider.canCheckOut && !provider.isLoading)
                            ? () => _checkAttendance('check_out')
                            : null,
                        icon: provider.isLoading
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  color: Colors.white,
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(Icons.logout),
                        label: Text(
                            provider.isLoading ? 'Đang xử lý...' : 'Check Out'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: provider.canCheckOut
                              ? AppColors.checkOut
                              : Colors.grey.shade400,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildRequestActions() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.assignment,
                  color: AppColors.primary,
                  size: 24,
                ),
                const SizedBox(width: 8),
                const Text(
                  'Yêu cầu & Đơn từ',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _navigateToLeaveRequest(),
                    icon: const Icon(Icons.event_available, size: 18),
                    label: const Text('Đơn nghỉ phép'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.info,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _navigateToAttendanceAdjustment(),
                    icon: const Icon(Icons.edit_calendar, size: 18),
                    label: const Text('Chỉnh công'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.secondary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _navigateToRequestsList(),
                icon: const Icon(Icons.list_alt, size: 18),
                label: const Text('Xem danh sách yêu cầu'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _navigateToLeaveRequest() async {
    try {
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => const LeaveRequestView(),
        ),
      );
    } catch (e) {
      _showSnackBar('Lỗi mở trang đơn nghỉ phép: $e', AppColors.error);
    }
  }

  Future<void> _navigateToAttendanceAdjustment() async {
    try {
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => const AttendanceAdjustmentView(),
        ),
      );
    } catch (e) {
      _showSnackBar('Lỗi mở trang chỉnh công: $e', AppColors.error);
    }
  }

  Future<void> _navigateToRequestsList() async {
    try {
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => const RequestsListView(),
        ),
      );
    } catch (e) {
      _showSnackBar('Lỗi mở danh sách yêu cầu: $e', AppColors.error);
    }
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

  Future<void> _checkAttendance(String action) async {
    final attendanceProvider = context.read<AttendanceProvider>();

    File? faceImage = await _openCamera(action);
    if (faceImage == null) return;

    String? wifiIp;
    try {
      wifiIp = await _wifiService.getWiFiIP();
    } catch (e) {
      wifiIp = null;
    }

    final success = await attendanceProvider.checkAttendance(
      action: action,
      faceImage: faceImage,
      wifiIp: wifiIp,
    );

    if (mounted) {
      if (success) {
        final successMessage = attendanceProvider.successMessage;
        if (successMessage != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.white),
                  const SizedBox(width: 8),
                  Expanded(child: Text(successMessage)),
                ],
              ),
              backgroundColor: AppColors.success,
              duration: const Duration(seconds: 3),
            ),
          );
        }
      } else {
        _showErrorDialog(
            context, attendanceProvider.error ?? 'Chấm công thất bại');
      }
    }
  }

  Future<File?> _openCamera(String action) async {
    File? capturedImage;

    try {
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => CameraView(
            action: action,
            onImageCaptured: (File image) {
              capturedImage = image;
            },
          ),
        ),
      );
    } catch (e) {
      // Handle camera error silently
    }

    return capturedImage;
  }

  void _showErrorDialog(BuildContext context, String errorMessage) {
    String title = '❌ Chấm công thất bại';
    String message = 'Đã xảy ra lỗi khi thực hiện chấm công.';
    String? details;
    List<String>? suggestions;
    VoidCallback? onRetry;

    // Phân tích lỗi để hiển thị thông tin phù hợp
    if (errorMessage.contains('Xác thực khuôn mặt thất bại')) {
      if (errorMessage.contains('Khuôn mặt không khớp')) {
        message =
            'Khuôn mặt không khớp với thông tin đã đăng ký trong hệ thống.';
        details = errorMessage.replaceAll('Xác thực khuôn mặt thất bại: ', '');
        suggestions = [
          'Đảm bảo chụp đúng khuôn mặt của bạn',
          'Ánh sáng phải đủ sáng và rõ ràng',
          'Khuôn mặt phải nằm gọn trong khung trắng',
          'Không đeo kính đen hoặc vật che khuôn mặt',
          'Thử lại hoặc liên hệ quản trị viên để đăng ký khuôn mặt mới'
        ];
        onRetry = () => _checkAttendance('check_in');
      } else if (errorMessage.contains('Không tìm thấy khuôn mặt')) {
        message = 'Không thể nhận diện khuôn mặt trong ảnh.';
        details = errorMessage.replaceAll('Xác thực khuôn mặt thất bại: ', '');
        suggestions = [
          'Đảm bảo khuôn mặt rõ ràng trong khung trắng',
          'Ánh sáng phải đủ sáng',
          'Không chụp quá xa hoặc quá gần',
          'Khuôn mặt phải chiếm phần lớn khung hình'
        ];
        onRetry = () => _checkAttendance('check_in');
      } else {
        message = 'Xác thực khuôn mặt thất bại.';
        details = errorMessage.replaceAll('Xác thực khuôn mặt thất bại: ', '');
        suggestions = [
          'Kiểm tra kết nối mạng',
          'Đảm bảo ánh sáng đủ sáng',
          'Thử lại hoặc liên hệ quản trị viên'
        ];
        onRetry = () => _checkAttendance('check_in');
      }
    } else if (errorMessage.contains('Không thể tạo bản ghi chấm công')) {
      message = 'Không thể tạo bản ghi chấm công trong hệ thống.';
      details = errorMessage;
      suggestions = [
        'Kiểm tra kết nối mạng',
        'Thử lại sau vài giây',
        'Liên hệ quản trị viên nếu vấn đề tiếp tục'
      ];
    } else {
      details = errorMessage;
      suggestions = [
        'Kiểm tra kết nối mạng',
        'Thử lại sau vài giây',
        'Liên hệ quản trị viên nếu vấn đề tiếp tục'
      ];
    }

    showDialog(
      context: context,
      builder: (context) => ErrorDialog(
        title: title,
        message: message,
        details: details,
        suggestions: suggestions,
        onRetry: onRetry,
      ),
    );
  }

  void _showLogoutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Đăng xuất'),
        content: const Text('Bạn có chắc chắn muốn đăng xuất?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Hủy'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              context.read<AuthProvider>().logout();
              Navigator.of(context).pushReplacementNamed('/login');
            },
            child: const Text('Đăng xuất'),
          ),
        ],
      ),
    );
  }
}
