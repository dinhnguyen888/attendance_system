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

class _CameraViewState extends State<CameraView> {
  final CameraService _cameraService = CameraService();
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
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
      decoration: BoxDecoration(
        border: Border.all(color: Colors.white, width: 2),
        borderRadius: BorderRadius.circular(20),
      ),
      margin: const EdgeInsets.all(40),
      child: const Center(
        child: Text(
          'Đặt khuôn mặt vào khung',
          style: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
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
      color: Colors.black,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          IconButton(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(Icons.close, color: Colors.white, size: 32),
          ),
          FloatingActionButton(
            onPressed: _captureImage,
            backgroundColor: AppColors.primary,
            child: const Icon(Icons.camera_alt, color: Colors.white, size: 32),
          ),
          IconButton(
            onPressed: _pickFromGallery,
            icon:
                const Icon(Icons.photo_library, color: Colors.white, size: 32),
          ),
        ],
      ),
    );
  }

  Future<void> _captureImage() async {
    final image = await _cameraService.takePicture();
    if (image != null && mounted) {
      widget.onImageCaptured(image);
      Navigator.pop(context);
    }
  }

  Future<void> _pickFromGallery() async {
    final image = await _cameraService.pickImageFromGallery();
    if (image != null && mounted) {
      widget.onImageCaptured(image);
      Navigator.pop(context);
    }
  }
}
