import 'employee.dart';

class LoginRequest {
  final String username;
  final String password;

  LoginRequest({
    required this.username,
    required this.password,
  });

  Map<String, dynamic> toJson() {
    return {
      'username': username,
      'password': password,
    };
  }
}

class LoginResponse {
  final bool success;
  final String message;
  final String? token;
  final Employee? employee;

  LoginResponse({
    required this.success,
    required this.message,
    this.token,
    this.employee,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    return LoginResponse(
      success: json['success'] ?? false,
      message: json['message'] ?? '',
      token: json['token'],
      employee:
          json['employee'] != null ? Employee.fromJson(json['employee']) : null,
    );
  }
}
