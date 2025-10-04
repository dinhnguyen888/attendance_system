import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/attendance_provider.dart';
import '../constants/app_colors.dart';
import '../models/attendance.dart';
import '../utils/date_time_utils.dart';

class AttendanceCard extends StatelessWidget {
  const AttendanceCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AttendanceProvider>(
      builder: (context, attendanceProvider, child) {
        final status = attendanceProvider.currentStatus;

        if (status == null) {
          return Card(
            elevation: 2,
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: EdgeInsets.all(20),
              child: Center(
                child: CircularProgressIndicator(),
              ),
            ),
          );
        }

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
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: _getStatusColor(status.status).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(
                        _getStatusIcon(status.status),
                        color: _getStatusColor(status.status),
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _getStatusTitle(status.status),
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _getFormattedStatusMessage(status),
                            style: const TextStyle(
                              fontSize: 14,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                _buildTimeInfo(status),
                if (status.totalHours > 0) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.success.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                      border:
                          Border.all(color: AppColors.success.withOpacity(0.3)),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.timer,
                          color: AppColors.success,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Tổng giờ làm việc: ${status.totalHours.toStringAsFixed(1)} giờ',
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: AppColors.success,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildTimeInfo(AttendanceStatus status) {
    return Row(
      children: [
        Expanded(
          child: _buildTimeItem(
            icon: Icons.login,
            label: 'Check In',
            time: status.checkIn,
            color: AppColors.checkIn,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildTimeItem(
            icon: Icons.logout,
            label: 'Check Out',
            time: status.checkOut,
            color: AppColors.checkOut,
          ),
        ),
      ],
    );
  }

  Widget _buildTimeItem({
    required IconData icon,
    required String label,
    required String? time,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 8),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            DateTimeUtils.formatTimeShort(time),
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: time != null
                  ? AppColors.textPrimary
                  : AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'not_started':
        return AppColors.warning;
      case 'working':
        return AppColors.working;
      case 'completed':
        return AppColors.completed;
      default:
        return AppColors.textSecondary;
    }
  }

  IconData _getStatusIcon(String status) {
    switch (status) {
      case 'not_started':
        return Icons.schedule;
      case 'working':
        return Icons.work;
      case 'completed':
        return Icons.check_circle;
      default:
        return Icons.help;
    }
  }

  String _getStatusTitle(String status) {
    switch (status) {
      case 'checked_out':
      case 'not_started':
        return 'Today';
      case 'checked_in':
      case 'working':
        return 'Đang làm việc';
      case 'completed':
        return 'Hoàn thành';
      case 'no_face_registered':
        return 'Chưa đăng ký';
      default:
        return 'Today';
    }
  }

  String _getFormattedStatusMessage(AttendanceStatus status) {
    switch (status.status) {
      case 'checked_in':
      case 'working':
        if (status.checkIn != null) {
          final formattedTime = DateTimeUtils.formatTime(status.checkIn);
          return 'Đã check-in lúc $formattedTime';
        }
        return status.message;
      case 'checked_out':
      case 'completed':
        if (status.checkOut != null) {
          final formattedTime = DateTimeUtils.formatTime(status.checkOut);
          return 'Đã check-out lúc $formattedTime';
        }
        return status.message;
      default:
        return status.message;
    }
  }
}
