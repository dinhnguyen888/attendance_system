class AppConstants {
  static const String appName = 'Attendance System';
  static const String appVersion = '1.0.0';

  static const String baseUrl = 'http://192.168.1.15:8069';
  static const String apiVersion = '/web';

  static const String odooLoginEndpoint = '/web/session/authenticate';
  static const String odooAttendanceCheckInEndpoint = '/attendance/check_in';
  static const String odooAttendanceCheckOutEndpoint = '/attendance/check_out';
  static const String odooAttendanceStatusEndpoint = '/attendance/status';
  static const String odooAttendanceHistoryEndpoint = '/attendance/history';
  static const String odooFaceRegisterEndpoint = '/attendance/register_face';
  static const String odooFaceHealthEndpoint = '/attendance/face_api_health';

  static const String tokenKey = 'auth_token';
  static const String userKey = 'user_data';

  static const int connectionTimeout = 30000;
  static const int receiveTimeout = 30000;

  static const String faceRecognitionApiUrl = 'http://192.168.1.15:8000';
  static const String faceRecognitionHealthEndpoint =
      '/face-recognition/health';
  static const String faceRecognitionRegisterEndpoint =
      '/face-recognition/register';
  static const String faceRecognitionVerifyEndpoint =
      '/face-recognition/verify';

  static const String defaultDateFormat = 'yyyy-MM-dd';
  static const String defaultTimeFormat = 'HH:mm:ss';
  static const String displayDateFormat = 'dd/MM/yyyy';
  static const String displayTimeFormat = 'HH:mm';
}
