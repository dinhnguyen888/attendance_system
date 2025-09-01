import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../constants/app_constants.dart';
import 'api_service.dart';

class FaceRecognitionService {
  static final FaceRecognitionService _instance =
      FaceRecognitionService._internal();
  factory FaceRecognitionService() => _instance;
  FaceRecognitionService._internal();

  final ApiService _apiService = ApiService();

  Future<Map<String, dynamic>> registerFace({
    required File faceImage,
  }) async {
    try {
      if (_apiService.sessionId == null) {
        return {
          'success': false,
          'message': 'Session không hợp lệ, vui lòng đăng nhập lại'
        };
      }

      final faceImageData =
          'data:image/jpeg;base64,${await _fileToBase64(faceImage)}';

      final registerData = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
          "face_image": faceImageData,
        }
      };

      final response = await http
          .post(
            Uri.parse(
                '${AppConstants.baseUrl}${AppConstants.odooFaceRegisterEndpoint}'),
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'Cookie': 'session_id=${_apiService.sessionId}',
            },
            body: jsonEncode(registerData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['result'] != null) {
          if (data['result']['success'] == true) {
            return {
              'success': true,
              'message':
                  data['result']['message'] ?? 'Đăng ký khuôn mặt thành công',
              'confidence': data['result']['confidence'] ?? 1.0,
              'action': data['result']['action'] ?? 'register',
            };
          } else {
            return {
              'success': false,
              'message':
                  data['result']['error'] ?? 'Đăng ký khuôn mặt thất bại',
            };
          }
        } else if (data['error'] != null) {
          return {
            'success': false,
            'message': data['error']['message'] ??
                data['error']['data']['message'] ??
                'Lỗi không xác định',
          };
        }
      }
      return {'success': false, 'message': 'Lỗi kết nối server'};
    } catch (e) {
      return {'success': false, 'message': 'Lỗi: $e'};
    }
  }

  Future<Map<String, dynamic>> checkFaceHealth() async {
    try {
      if (_apiService.sessionId == null) {
        return {'success': false, 'error': 'Session không hợp lệ'};
      }

      final healthData = {"jsonrpc": "2.0", "method": "call", "params": {}};

      final response = await http
          .post(
            Uri.parse(
                '${AppConstants.baseUrl}${AppConstants.odooFaceHealthEndpoint}'),
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'Cookie': 'session_id=${_apiService.sessionId}',
            },
            body: jsonEncode(healthData),
          )
          .timeout(Duration(milliseconds: AppConstants.connectionTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['result'] != null) {
          return data['result'];
        }
      }
      return {'success': false, 'error': 'Health check failed'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  Future<String> _fileToBase64(File file) async {
    final bytes = await file.readAsBytes();
    return base64Encode(bytes);
  }
}
