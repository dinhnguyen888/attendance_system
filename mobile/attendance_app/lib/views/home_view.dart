import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import '../providers/auth_provider.dart';
import '../providers/attendance_provider.dart';
import '../constants/app_colors.dart';
import '../widgets/custom_button.dart';
import '../widgets/attendance_card.dart';
import '../widgets/profile_card.dart';
import '../widgets/attendance_calendar.dart';
import 'camera_view.dart';

class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AttendanceProvider>().loadAttendanceStatus();
      context.read<AttendanceProvider>().loadAttendanceCalendar();
      context.read<AuthProvider>().refreshUserProfile();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: _buildAppBar(),
      body: RefreshIndicator(
        onRefresh: () async {
          await context.read<AttendanceProvider>().loadAttendanceStatus();
          await context.read<AttendanceProvider>().loadAttendanceCalendar();
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
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Chấm Công',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: CustomButton(
                    onPressed: () => _checkAttendance('check_in'),
                    text: 'Check In',
                    backgroundColor: AppColors.checkIn,
                    textColor: Colors.white,
                    icon: Icons.login,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: CustomButton(
                    onPressed: () => _checkAttendance('check_out'),
                    text: 'Check Out',
                    backgroundColor: AppColors.checkOut,
                    textColor: Colors.white,
                    icon: Icons.logout,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _checkAttendance(String action) async {
    final authProvider = context.read<AuthProvider>();
    final attendanceProvider = context.read<AttendanceProvider>();

    if (authProvider.currentUser != null) {
      File? faceImage;

      if (action == 'check_in' || action == 'check_out') {
        faceImage = await _showCameraDialog(action);
        if (faceImage == null) return;
      }

      final success = await attendanceProvider.checkAttendance(
        employeeId: authProvider.currentUser!.id,
        action: action,
        faceImage: faceImage,
      );

      if (success && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              action == 'check_in'
                  ? 'Check-in thành công!'
                  : 'Check-out thành công!',
            ),
            backgroundColor: AppColors.success,
          ),
        );
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(attendanceProvider.error ?? 'Chấm công thất bại'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Future<File?> _showCameraDialog(String action) async {
    File? capturedImage;

    final method = await showDialog<String>(
      context: context,
      builder: (BuildContext context) => AlertDialog(
        title:
            Text('Chụp ảnh ${action == 'check_in' ? 'Check-in' : 'Check-out'}'),
        content: const Text('Chọn phương thức chụp ảnh:'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, 'camera'),
            child: const Text('Camera'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, 'gallery'),
            child: const Text('Thư viện'),
          ),
        ],
      ),
    );

    if (method == 'camera') {
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
        print('❌ Camera error, falling back to gallery: $e');
        capturedImage = await _pickFromGallery();
      }
    } else if (method == 'gallery') {
      capturedImage = await _pickFromGallery();
    }

    return capturedImage;
  }

  Future<File?> _pickFromGallery() async {
    try {
      final picker = ImagePicker();
      final pickedFile = await picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 80,
      );
      if (pickedFile != null) {
        return File(pickedFile.path);
      }
    } catch (e) {
      print('❌ Gallery pick error: $e');
    }
    return null;
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
