import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import '../services/camera_service.dart';
import '../constants/app_colors.dart';

class CameraView extends StatefulWidget {
  final String action;
  final Function(File) onImageCaptured;

  const CameraView({
    super.key,
    required this.action,
    required this.onImageCaptured,
  });

  @override
  State<CameraView> createState() => _CameraViewState();
}

class _CameraViewState extends State<CameraView> with TickerProviderStateMixin {
  final CameraService _cameraService = CameraService();
  bool _isLoading = true;
  bool _isCapturing = false;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat();
    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    await _cameraService.initialize();
    if (mounted) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _cameraService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text(
            'Chụp ảnh ${widget.action == 'check_in' ? 'Check-in' : 'Check-out'}'),
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.white))
          : _cameraService.isInitialized
              ? _buildCameraView()
              : _buildErrorView(),
      bottomNavigationBar: _buildBottomBar(),
    );
  }

  Widget _buildCameraView() {
    return Stack(
      children: [
        CameraPreview(_cameraService.controller!),
        _buildOverlay(),
      ],
    );
  }

  Widget _buildOverlay() {
    return Container(
      child: Stack(
        children: [
          Center(
            child: AnimatedBuilder(
              animation: _pulseAnimation,
              builder: (context, child) {
                return Transform.scale(
                  scale: _pulseAnimation.value,
                  child: Container(
                    width: 280,
                    height: 380,
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: AppColors.primary.withOpacity(0.8),
                        width: 3,
                      ),
                      borderRadius: BorderRadius.circular(140),
                    ),
                  ),
                );
              },
            ),
          ),
          Center(
            child: Container(
              width: 250,
              height: 350,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white, width: 2),
                borderRadius: BorderRadius.circular(125),
              ),
            ),
          ),
          Positioned(
            top: 100,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              margin: const EdgeInsets.symmetric(horizontal: 40),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.7),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.face,
                    color: AppColors.primary,
                    size: 32,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Đặt khuôn mặt vào khung',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Đảm bảo ánh sáng đủ sáng và khuôn mặt rõ ràng',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 12,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorView() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error, color: Colors.white, size: 64),
          SizedBox(height: 16),
          Text(
            'Không thể khởi tạo camera',
            style: TextStyle(color: Colors.white, fontSize: 18),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomBar() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.black,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            Container(
              decoration: BoxDecoration(
                color: Colors.grey.withOpacity(0.3),
                shape: BoxShape.circle,
              ),
              child: IconButton(
                onPressed: _isCapturing ? null : () => Navigator.pop(context),
                icon: const Icon(Icons.close, color: Colors.white, size: 28),
              ),
            ),
            GestureDetector(
              onTap: _isCapturing ? null : _captureImage,
              child: Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: _isCapturing ? Colors.grey : AppColors.primary,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withOpacity(0.3),
                      blurRadius: 15,
                      spreadRadius: 2,
                    ),
                  ],
                ),
                child: _isCapturing
                    ? const CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 3,
                      )
                    : const Icon(
                        Icons.camera_alt,
                        color: Colors.white,
                        size: 36,
                      ),
              ),
            ),
            Container(
              decoration: BoxDecoration(
                color: Colors.grey.withOpacity(0.3),
                shape: BoxShape.circle,
              ),
              child: IconButton(
                onPressed: _isCapturing ? null : _switchCamera,
                icon: const Icon(Icons.flip_camera_ios,
                    color: Colors.white, size: 28),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _captureImage() async {
    if (_isCapturing) return;

    setState(() {
      _isCapturing = true;
    });

    try {
      final image = await _cameraService.takePicture();
      if (image != null && mounted) {
        widget.onImageCaptured(image);
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Lỗi chụp ảnh: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isCapturing = false;
        });
      }
    }
  }

  Future<void> _switchCamera() async {
    try {
      _cameraService.dispose();
      await _cameraService.initialize();
      setState(() {});
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Không thể chuyển camera: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
}
