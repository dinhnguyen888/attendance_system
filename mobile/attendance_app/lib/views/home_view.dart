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
import '../widgets/error_dialog.dart';

class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  final WiFiService _wifiService = WiFiService();
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
    } catch (e) {
      print('Error initializing data: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: _buildAppBar(),
      body: RefreshIndicator(
        onRefresh: () async {
          await context.read<AttendanceProvider>().initialize();
        },
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
              const AttendanceCalendar(),
            ],
          ),
        ),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text(
        'Attendance System',
        style: TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
        ),
      ),
      backgroundColor: AppColors.primary,
      elevation: 0,
      actions: [
        IconButton(
          icon: const Icon(Icons.logout, color: Colors.white),
          onPressed: () => _showLogoutDialog(),
        ),
      ],
    );
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
                if (provider.needsFaceRegistration) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.orange.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.orange.shade200),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.warning,
                            color: Colors.orange.shade600, size: 20),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Bạn cần đăng ký khuôn mặt trước khi chấm công',
                            style: TextStyle(
                              color: Colors.orange.shade700,
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed:
                          provider.isLoading ? null : () => _registerFace(),
                      icon: provider.isLoading
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2,
                              ),
                            )
                          : const Icon(Icons.face),
                      label: Text(provider.isLoading
                          ? 'Đang xử lý...'
                          : 'Đăng Ký Khuôn Mặt'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                ] else ...[
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed:
                              (provider.canCheckIn && !provider.isLoading)
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
                          label: Text(provider.isLoading
                              ? 'Đang xử lý...'
                              : 'Check In'),
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
                          onPressed:
                              (provider.canCheckOut && !provider.isLoading)
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
                          label: Text(provider.isLoading
                              ? 'Đang xử lý...'
                              : 'Check Out'),
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
              ],
            ),
          ),
        );
      },
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

  Future<void> _registerFace() async {
    final attendanceProvider = context.read<AttendanceProvider>();

    File? faceImage = await _openCamera('register');
    if (faceImage == null) return;

    final success = await attendanceProvider.registerFace(faceImage);

    if (mounted) {
      if (success) {
        final successMessage = attendanceProvider.successMessage;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                Icon(Icons.check_circle, color: Colors.white),
                const SizedBox(width: 8),
                Expanded(
                  child:
                      Text(successMessage ?? 'Đăng ký khuôn mặt thành công!'),
                ),
              ],
            ),
            backgroundColor: AppColors.success,
            duration: const Duration(seconds: 3),
          ),
        );
      } else {
        _showErrorDialog(
            context, attendanceProvider.error ?? 'Đăng ký khuôn mặt thất bại');
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
