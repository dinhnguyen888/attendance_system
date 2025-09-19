import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants/app_constants.dart';
import '../models/employee.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  late SharedPreferences _preferences;

  Future<void> initialize() async {
    _preferences = await SharedPreferences.getInstance();
  }

  Future<void> saveToken(String token) async {
    final displayToken =
        token.length > 20 ? '${token.substring(0, 20)}...' : token;
    print('💾 Đang lưu token: $displayToken');
    await _secureStorage.write(key: AppConstants.tokenKey, value: token);
    print('✅ Token đã được lưu');
  }

  Future<String?> getToken() async {
    final token = await _secureStorage.read(key: AppConstants.tokenKey);
    if (token != null) {
      final displayToken =
          token.length > 20 ? '${token.substring(0, 20)}...' : token;
      print('🔍 Đọc token: $displayToken');
    } else {
      print('🔍 Đọc token: null');
    }
    return token;
  }

  Future<void> removeToken() async {
    await _secureStorage.delete(key: AppConstants.tokenKey);
  }

  Future<void> saveUser(Employee user) async {
    print('💾 Đang lưu user: ${user.name}');
    await _preferences.setString(
        AppConstants.userKey, jsonEncode(user.toJson()));
    print('✅ User đã được lưu');
  }

  Future<Employee?> getUser() async {
    final userData = _preferences.getString(AppConstants.userKey);
    if (userData != null) {
      final user = Employee.fromJson(jsonDecode(userData));
      print('🔍 Đọc user: ${user.name}');
      return user;
    }
    print('🔍 Không tìm thấy user data');
    return null;
  }

  Future<void> removeUser() async {
    await _preferences.remove(AppConstants.userKey);
  }

  Future<void> clearAll() async {
    await _secureStorage.deleteAll();
    await _preferences.clear();
  }

  Future<bool> isLoggedIn() async {
    final token = await getToken();
    final isLoggedIn = token != null && token.isNotEmpty;
    print(
        '🔑 Kiểm tra đăng nhập: $isLoggedIn (token: ${token != null ? 'có' : 'không'})');
    return isLoggedIn;
  }
}
