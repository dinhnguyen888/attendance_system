import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../models/employee.dart';
import '../constants/app_colors.dart';

class ProfileCard extends StatelessWidget {
  const ProfileCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        final user = authProvider.currentUser;
        if (user == null) return const SizedBox.shrink();

        return Card(
          elevation: 4,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  AppColors.primary,
                  AppColors.primaryDark,
                ],
              ),
            ),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildHeaderSection(user),
                  const SizedBox(height: 20),
                  _buildBasicInfoSection(user),
                  const SizedBox(height: 16),
                  _buildContactInfoSection(user),
                  const SizedBox(height: 16),
                  _buildOrganizationalInfoSection(user),
                  if (_shouldShowManager(user)) ...[
                    const SizedBox(height: 16),
                    _buildManagerSection(user),
                  ],
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildHeaderSection(Employee user) {
    return Row(
      children: [
        CircleAvatar(
          radius: 30,
          backgroundColor: Colors.white.withOpacity(0.2),
          child: Text(
            user.name != 'Chưa có'
                ? user.name.substring(0, 1).toUpperCase()
                : 'E',
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                user.name != 'Chưa có' ? user.name : 'Employee A',
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                user.position != 'Chưa có' ? user.position : 'Chưa có',
                style: TextStyle(
                  fontSize: 14,
                  color: user.position != 'Chưa có'
                      ? Colors.white70
                      : Colors.white60,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                user.department != 'Chưa có' ? user.department : 'Chưa có',
                style: TextStyle(
                  fontSize: 12,
                  color: user.department != 'Chưa có'
                      ? Colors.white60
                      : Colors.white54,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildBasicInfoSection(Employee user) {
    return Row(
      children: [
        Expanded(
          child: _buildInfoItem(
            icon: Icons.badge,
            label: 'Mã NV',
            value:
                user.employeeCode != 'Chưa có' ? user.employeeCode : 'Chưa có',
            valueColor:
                user.employeeCode != 'Chưa có' ? Colors.white : Colors.white70,
          ),
        ),
        Expanded(
          child: _buildInfoItem(
            icon: Icons.face,
            label: 'Khuôn mặt',
            value: user.faceRegistered ? 'Đã đăng ký' : 'Chưa đăng ký',
            valueColor: user.faceRegistered ? Colors.green : Colors.orange,
          ),
        ),
      ],
    );
  }

  Widget _buildContactInfoSection(Employee user) {
    return Row(
      children: [
        Expanded(
          child: _buildInfoItem(
            icon: Icons.email,
            label: 'Email',
            value: user.email != 'Chưa có' ? user.email : 'Chưa có',
            valueColor: user.email != 'Chưa có' ? Colors.white : Colors.white70,
          ),
        ),
        Expanded(
          child: _buildInfoItem(
            icon: Icons.phone,
            label: 'SĐT',
            value: user.phone != 'Chưa có' ? user.phone : 'Chưa có',
            valueColor: user.phone != 'Chưa có' ? Colors.white : Colors.white70,
          ),
        ),
      ],
    );
  }

  Widget _buildOrganizationalInfoSection(Employee user) {
    return Row(
      children: [
        Expanded(
          child: _buildInfoItem(
            icon: Icons.business,
            label: 'Phòng ban',
            value: user.department != 'Chưa có' ? user.department : 'Chưa có',
            valueColor:
                user.department != 'Chưa có' ? Colors.white : Colors.white70,
          ),
        ),
        Expanded(
          child: _buildInfoItem(
            icon: Icons.work,
            label: 'Manager',
            value: user.position != 'Chưa có' ? user.position : 'Chưa có',
            valueColor:
                user.position != 'Chưa có' ? Colors.white : Colors.white70,
          ),
        ),
      ],
    );
  }

  Widget _buildManagerSection(Employee user) {
    return Row(
      children: [
        Expanded(
          child: _buildInfoItem(
            icon: Icons.person_pin,
            label: 'Quản lý trực tiếp',
            value: user.manager!,
            valueColor: Colors.white,
          ),
        ),
        const Expanded(child: SizedBox()),
      ],
    );
  }

  bool _shouldShowManager(Employee user) {
    return user.manager != null &&
        user.manager!.isNotEmpty &&
        user.manager != 'Chưa có';
  }

  Widget _buildInfoItem({
    required IconData icon,
    required String label,
    required String value,
    Color? valueColor,
  }) {
    final isValueEmpty = value == 'Chưa có';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 16, color: Colors.white70),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: valueColor ?? (isValueEmpty ? Colors.white70 : Colors.white),
            fontStyle: isValueEmpty ? FontStyle.italic : FontStyle.normal,
          ),
        ),
      ],
    );
  }
}
