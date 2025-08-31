class AppConstants {
  static const String appName = 'Attendance System';
  static const String appVersion = '1.0.0';

  static const String baseUrl = 'http://192.168.1.15:8069';
  static const String apiVersion = '/web';

  static const String loginEndpoint = '/session/authenticate';
  static const String profileEndpoint = '/web/dataset/call_kw/res.users/read';
  static const String attendanceHistoryEndpoint =
      '/web/dataset/call_kw/hr.attendance/search_read';
  static const String attendanceCheckEndpoint =
      '/web/dataset/call_kw/hr.attendance/create';
  static const String attendanceStatusEndpoint =
      '/web/dataset/call_kw/hr.attendance/search_read';
  static const String attendanceStatisticsEndpoint =
      '/web/dataset/call_kw/hr.attendance/read_group';

  static const String tokenKey = 'auth_token';
  static const String userKey = 'user_data';

  static const int connectionTimeout = 10000;
  static const int receiveTimeout = 10000;

  static const String defaultDateFormat = 'yyyy-MM-dd';
  static const String defaultTimeFormat = 'HH:mm:ss';
  static const String displayDateFormat = 'dd/MM/yyyy';
  static const String displayTimeFormat = 'HH:mm';
}
