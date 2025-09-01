import 'package:flutter/foundation.dart';
import '../models/employee.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();

  bool _isLoading = false;
  bool _isLoggedIn = false;
  Employee? _currentUser;
  String? _error;

  bool get isLoading => _isLoading;
  bool get isLoggedIn => _isLoggedIn;
  Employee? get currentUser => _currentUser;
  String? get error => _error;

  AuthProvider() {
    _initializeAuth();
  }

  Future<void> _initializeAuth() async {
    await _storageService.initialize();
    final isLoggedIn = await _storageService.isLoggedIn();
    if (isLoggedIn) {
      final token = await _storageService.getToken();
      final user = await _storageService.getUser();
      if (token != null && user != null) {
        _apiService.setToken(token);
        _currentUser = user;
        _isLoggedIn = true;
        notifyListeners();
      }
    }
  }

  Future<bool> login(String username, String password) async {
    try {
      _setLoading(true);
      _clearError();

      if (username.trim().isEmpty || password.isEmpty) {
        _setError('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu');
        return false;
      }

      final response = await _apiService.login(username, password);

      if (response.success &&
          response.token != null &&
          response.employee != null) {
        try {
          await _storageService.saveToken(response.token!);
          await _storageService.saveUser(response.employee!);

          _apiService.setToken(response.token!);
          _currentUser = response.employee;
          _isLoggedIn = true;
          notifyListeners();

          try {
            final detailedProfile = await _apiService.getCurrentUserProfile();
            if (detailedProfile != null) {
              _currentUser = detailedProfile;
              await _storageService.saveUser(detailedProfile);
              notifyListeners();
            }
          } catch (e) {
            print('Không thể tải profile chi tiết: $e');
          }

          return true;
        } catch (e) {
          _setError('Lỗi khi lưu thông tin đăng nhập. Vui lòng thử lại.');
          return false;
        }
      } else {
        _setError(_getErrorMessage(response.message));
        return false;
      }
    } catch (e) {
      _setError(_getErrorMessage(e.toString()));
      return false;
    } finally {
      _setLoading(false);
    }
  }

  String _getErrorMessage(String error) {
    if (error.contains('SocketException') ||
        error.contains('NetworkException')) {
      return 'Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng.';
    }
    if (error.contains('TimeoutException')) {
      return 'Kết nối bị timeout. Vui lòng thử lại.';
    }
    if (error.contains('401') || error.contains('Unauthorized')) {
      return 'Tên đăng nhập hoặc mật khẩu không đúng.';
    }
    if (error.contains('404') || error.contains('Not Found')) {
      return 'Không tìm thấy tài khoản. Vui lòng kiểm tra lại.';
    }
    if (error.contains('500') || error.contains('Internal Server Error')) {
      return 'Lỗi server. Vui lòng thử lại sau.';
    }
    if (error.contains('Tên đăng nhập hoặc mật khẩu không đúng')) {
      return 'Tên đăng nhập hoặc mật khẩu không đúng.';
    }
    return error.isNotEmpty ? error : 'Đăng nhập thất bại. Vui lòng thử lại.';
  }

  Future<void> logout() async {
    try {
      await _storageService.clearAll();
      _apiService.setToken('');
      _currentUser = null;
      _isLoggedIn = false;
      notifyListeners();
    } catch (e) {
      _setError(e.toString());
    }
  }

  Future<void> refreshUserProfile() async {
    try {
      if (_currentUser != null) {
        // First try to refresh session
        try {
          await _apiService.refreshSession();
        } catch (e) {
          print('⚠️ Session refresh failed: $e');
          if (e.toString().contains('Session hết hạn')) {
            print('🔄 Session expired, logging out user');
            await logout();
            return;
          }
        }

        // Then try to get updated profile
        final updatedUser = await _apiService.getCurrentUserProfile();
        if (updatedUser != null) {
          _currentUser = updatedUser;
          await _storageService.saveUser(updatedUser);
          notifyListeners();
        }
      }
    } catch (e) {
      print('⚠️ Error refreshing profile: $e');
      if (e.toString().contains('Session hết hạn')) {
        print('🔄 Session expired, logging out user');
        await logout();
      } else {
        _setError('Không thể cập nhật thông tin profile: $e');
      }
    }
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String error) {
    _error = error;
    notifyListeners();
  }

  void _clearError() {
    _error = null;
    notifyListeners();
  }

  void clearError() {
    _clearError();
  }
}
