import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../constants/app_colors.dart';
import '../models/attendance_adjustment.dart';
import '../services/attendance_adjustment_service.dart';
import '../widgets/custom_button.dart';
import '../widgets/custom_text_field.dart';

class AttendanceAdjustmentView extends StatefulWidget {
  const AttendanceAdjustmentView({super.key});

  @override
  State<AttendanceAdjustmentView> createState() =>
      _AttendanceAdjustmentViewState();
}

class _AttendanceAdjustmentViewState extends State<AttendanceAdjustmentView> {
  final _formKey = GlobalKey<FormState>();
  final _adjustmentService = AttendanceAdjustmentService();

  final _reasonController = TextEditingController();
  final _originalCheckInController = TextEditingController();
  final _originalCheckOutController = TextEditingController();
  final _requestedCheckInController = TextEditingController();
  final _requestedCheckOutController = TextEditingController();

  DateTime? _selectedDate;
  bool _isLoading = false;

  @override
  void dispose() {
    _reasonController.dispose();
    _originalCheckInController.dispose();
    _originalCheckOutController.dispose();
    _requestedCheckInController.dispose();
    _requestedCheckOutController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: _buildAppBar(),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildInfoCard(),
              const SizedBox(height: 24),
              _buildDateCard(),
              const SizedBox(height: 24),
              _buildTimeAdjustmentCard(),
              const SizedBox(height: 24),
              _buildReasonCard(),
              const SizedBox(height: 32),
              _buildSubmitButton(),
            ],
          ),
        ),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text(
        'Yêu cầu chỉnh công',
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
    );
  }

  Widget _buildInfoCard() {
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
                Icon(Icons.info_outline, color: AppColors.info, size: 24),
                const SizedBox(width: 8),
                const Text(
                  'Thông tin',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            const Text(
              'Yêu cầu chỉnh công sẽ được gửi đến quản lý trực tiếp và HR để duyệt. Vui lòng điền đầy đủ thông tin.',
              style: TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDateCard() {
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
                Icon(Icons.calendar_today, color: AppColors.primary, size: 24),
                const SizedBox(width: 8),
                const Text(
                  'Ngày cần chỉnh',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            InkWell(
              onTap: _selectDate,
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                ),
                child: Row(
                  children: [
                    Icon(Icons.calendar_month,
                        color: AppColors.primary, size: 20),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _selectedDate != null
                            ? '${_selectedDate!.day}/${_selectedDate!.month}/${_selectedDate!.year}'
                            : 'Chọn ngày cần chỉnh công',
                        style: TextStyle(
                          fontSize: 16,
                          color: _selectedDate != null
                              ? AppColors.textPrimary
                              : AppColors.textHint,
                          fontWeight: _selectedDate != null
                              ? FontWeight.w600
                              : FontWeight.normal,
                        ),
                      ),
                    ),
                    Icon(Icons.arrow_drop_down, color: AppColors.textSecondary),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimeAdjustmentCard() {
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
                Icon(Icons.access_time, color: AppColors.primary, size: 24),
                const SizedBox(width: 8),
                const Text(
                  'Thời gian chấm công',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _buildTimeSection(
              title: 'Thời gian hiện tại',
              checkInController: _originalCheckInController,
              checkOutController: _originalCheckOutController,
              isReadOnly: false,
            ),
            const SizedBox(height: 20),
            _buildTimeSection(
              title: 'Thời gian yêu cầu chỉnh',
              checkInController: _requestedCheckInController,
              checkOutController: _requestedCheckOutController,
              isReadOnly: false,
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.warning.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.warning.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  Icon(Icons.warning, color: AppColors.warning, size: 16),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Để trống nếu không cần chỉnh thời gian đó',
                      style: TextStyle(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimeSection({
    required String title,
    required TextEditingController checkInController,
    required TextEditingController checkOutController,
    required bool isReadOnly,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: CustomTextField(
                controller: checkInController,
                labelText: 'Check In',
                hintText: 'HH:MM',
                keyboardType: TextInputType.datetime,
                enabled: !isReadOnly,
                validator: (value) {
                  if (value != null && value.isNotEmpty) {
                    if (!_isValidTimeFormat(value)) {
                      return 'Định dạng: HH:MM';
                    }
                  }
                  return null;
                },
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: CustomTextField(
                controller: checkOutController,
                labelText: 'Check Out',
                hintText: 'HH:MM',
                keyboardType: TextInputType.datetime,
                enabled: !isReadOnly,
                validator: (value) {
                  if (value != null && value.isNotEmpty) {
                    if (!_isValidTimeFormat(value)) {
                      return 'Định dạng: HH:MM';
                    }
                  }
                  return null;
                },
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildReasonCard() {
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
                Icon(Icons.edit_note, color: AppColors.primary, size: 24),
                const SizedBox(width: 8),
                const Text(
                  'Lý do chỉnh công',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            CustomTextField(
              controller: _reasonController,
              labelText: 'Lý do chỉnh công',
              hintText: 'Nhập lý do cần chỉnh công...',
              maxLines: 4,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Vui lòng nhập lý do chỉnh công';
                }
                if (value.trim().length < 10) {
                  return 'Lý do chỉnh công phải có ít nhất 10 ký tự';
                }
                return null;
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSubmitButton() {
    return CustomButton(
      onPressed: _isLoading ? null : _submitAdjustmentRequest,
      text: 'Gửi yêu cầu chỉnh công',
      isLoading: _isLoading,
      backgroundColor: AppColors.primary,
      icon: Icons.send,
    );
  }

  Future<void> _selectDate() async {
    final now = DateTime.now();
    final firstDate = now.subtract(const Duration(days: 30));
    final lastDate = now.add(const Duration(days: 30));

    final selectedDate = await showDatePicker(
      context: context,
      initialDate: _selectedDate ?? now,
      firstDate: firstDate,
      lastDate: lastDate,
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: AppColors.primary,
              onPrimary: Colors.white,
              surface: AppColors.surface,
              onSurface: AppColors.textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );

    if (selectedDate != null) {
      setState(() => _selectedDate = selectedDate);
    }
  }

  bool _isValidTimeFormat(String time) {
    final timeRegex = RegExp(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$');
    return timeRegex.hasMatch(time);
  }

  Future<void> _submitAdjustmentRequest() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedDate == null) {
      _showSnackBar('Vui lòng chọn ngày cần chỉnh công', AppColors.warning);
      return;
    }

    final hasOriginalTime = _originalCheckInController.text.isNotEmpty ||
        _originalCheckOutController.text.isNotEmpty;
    final hasRequestedTime = _requestedCheckInController.text.isNotEmpty ||
        _requestedCheckOutController.text.isNotEmpty;

    if (!hasOriginalTime && !hasRequestedTime) {
      _showSnackBar(
          'Vui lòng nhập ít nhất một thời gian cần chỉnh', AppColors.warning);
      return;
    }

    setState(() => _isLoading = true);

    try {
      final adjustment = await _adjustmentService.createAttendanceAdjustment(
        date: _selectedDate!.toIso8601String().split('T')[0],
        originalCheckIn: _originalCheckInController.text.isNotEmpty
            ? _originalCheckInController.text
            : null,
        originalCheckOut: _originalCheckOutController.text.isNotEmpty
            ? _originalCheckOutController.text
            : null,
        requestedCheckIn: _requestedCheckInController.text.isNotEmpty
            ? _requestedCheckInController.text
            : null,
        requestedCheckOut: _requestedCheckOutController.text.isNotEmpty
            ? _requestedCheckOutController.text
            : null,
        reason: _reasonController.text.trim(),
      );

      if (mounted) {
        _showSnackBar(
            'Yêu cầu chỉnh công đã được gửi thành công!', AppColors.success);
        Navigator.pop(context, adjustment);
      }
    } catch (e) {
      if (mounted) {
        _showSnackBar('Gửi yêu cầu chỉnh công thất bại: $e', AppColors.error);
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _showSnackBar(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              color == AppColors.success
                  ? Icons.check_circle
                  : color == AppColors.warning
                      ? Icons.warning
                      : Icons.error,
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
