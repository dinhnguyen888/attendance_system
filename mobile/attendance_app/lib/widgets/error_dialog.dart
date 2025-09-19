import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

class ErrorDialog extends StatelessWidget {
  final String title;
  final String message;
  final String? details;
  final List<String>? suggestions;
  final VoidCallback? onRetry;
  final VoidCallback? onClose;

  const ErrorDialog({
    Key? key,
    required this.title,
    required this.message,
    this.details,
    this.suggestions,
    this.onRetry,
    this.onClose,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      title: Row(
        children: [
          Icon(
            Icons.error_outline,
            color: AppColors.error,
            size: 28,
          ),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              title,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: AppColors.error,
              ),
            ),
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message,
              style: TextStyle(
                fontSize: 16,
                color: Colors.black87,
              ),
            ),
            if (details != null) ...[
              SizedBox(height: 16),
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '🔍 Chi tiết lỗi:',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        color: Colors.grey[700],
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      details!,
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.grey[600],
                        fontFamily: 'monospace',
                      ),
                    ),
                  ],
                ),
              ),
            ],
            if (suggestions != null && suggestions!.isNotEmpty) ...[
              SizedBox(height: 16),
              Text(
                '💡 Hướng dẫn khắc phục:',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                  color: Colors.grey[700],
                ),
              ),
              SizedBox(height: 8),
              ...suggestions!.map((suggestion) => Padding(
                    padding: EdgeInsets.only(bottom: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('• ', style: TextStyle(color: AppColors.primary)),
                        Expanded(
                          child: Text(
                            suggestion,
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey[600],
                            ),
                          ),
                        ),
                      ],
                    ),
                  )),
            ],
          ],
        ),
      ),
      actions: [
        if (onRetry != null)
          TextButton(
            onPressed: onRetry,
            child: Text(
              '🔄 Thử lại',
              style: TextStyle(
                color: AppColors.primary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        TextButton(
          onPressed: onClose ?? () => Navigator.of(context).pop(),
          child: Text(
            'Đóng',
            style: TextStyle(
              color: Colors.grey[600],
            ),
          ),
        ),
      ],
    );
  }
}
