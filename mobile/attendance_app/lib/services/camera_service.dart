import 'dart:io';
import 'package:camera/camera.dart';
import 'permission_service.dart';

class CameraService {
  static final CameraService _instance = CameraService._internal();
  factory CameraService() => _instance;
  CameraService._internal();

  final PermissionService _permissionService = PermissionService();
  CameraController? _controller;
  List<CameraDescription>? _cameras;
  bool _isInitialized = false;

  CameraController? get controller => _controller;
  List<CameraDescription>? get cameras => _cameras;
  bool get isInitialized => _isInitialized;

  Future<void> initialize() async {
    try {
      final hasPermission = await _permissionService.requestCameraPermission();
      if (!hasPermission) {
        _isInitialized = false;
        return;
      }

      _cameras = await availableCameras();
      if (_cameras != null && _cameras!.isNotEmpty) {
        CameraDescription frontCamera = _cameras!.firstWhere(
          (camera) => camera.lensDirection == CameraLensDirection.front,
          orElse: () => _cameras![0],
        );

        _controller = CameraController(
          frontCamera,
          ResolutionPreset.medium,
          enableAudio: false,
          imageFormatGroup: ImageFormatGroup.bgra8888,
        );

        _controller!.addListener(() {
          if (_controller!.value.hasError) {
            print(
                '❌ Camera controller error: ${_controller!.value.errorDescription}');
            _isInitialized = false;
            _controller = null;
          }
        });

        await _controller!.initialize();
        _isInitialized = true;

        if (_controller!.value.hasError) {
          print(
              '❌ Camera initialization failed: ${_controller!.value.errorDescription}');
          _isInitialized = false;
          _controller = null;
        }
      }
    } catch (e) {
      print('❌ Camera initialization error: $e');
      _isInitialized = false;
      _controller = null;

      if (e.toString().contains('Invalid external texture')) {
        print('🔄 Attempting to reinitialize camera due to texture error...');
        await Future.delayed(Duration(milliseconds: 1000));
        try {
          await initialize();
        } catch (retryError) {
          print('❌ Camera reinitialization failed: $retryError');
        }
      }
    }
  }

  Future<File?> takePicture() async {
    if (!_isInitialized || _controller == null) return null;

    try {
      if (_controller!.value.hasError) {
        print(
            '❌ Camera has error before capture: ${_controller!.value.errorDescription}');
        await reinitialize();
        return null;
      }

      final image = await _controller!.takePicture();
      return File(image.path);
    } catch (e) {
      print('❌ Camera capture error: $e');
      await reinitialize();
      return null;
    }
  }

  void dispose() {
    _controller?.dispose();
    _controller = null;
    _isInitialized = false;
  }

  Future<void> reinitialize() async {
    dispose();
    await Future.delayed(Duration(milliseconds: 500));
    await initialize();
  }
}
