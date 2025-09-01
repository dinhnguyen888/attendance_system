import 'package:intl/intl.dart';

class DateTimeUtils {
  static final DateFormat _timeFormat = DateFormat('HH:mm:ss');
  static final DateFormat _dateFormat = DateFormat('dd/MM/yyyy');
  static final DateFormat _dateTimeFormat = DateFormat('dd/MM/yyyy HH:mm:ss');

  static DateTime? parseIsoString(String? isoString) {
    if (isoString == null || isoString.isEmpty) return null;
    try {
      DateTime dateTime;

      if (isoString.contains('+07:00') || isoString.contains('Z')) {
        dateTime = DateTime.parse(isoString);
      } else {
        dateTime = DateTime.parse(isoString + 'Z');
      }

      return dateTime.toLocal();
    } catch (e) {
      print('Error parsing ISO string: $isoString - $e');
      return null;
    }
  }

  static String formatTime(String? isoString) {
    final dateTime = parseIsoString(isoString);
    if (dateTime == null) return '--:--:--';

    return _timeFormat.format(dateTime);
  }

  static String formatTimeShort(String? isoString) {
    final dateTime = parseIsoString(isoString);
    if (dateTime == null) return '--:--';

    return DateFormat('HH:mm').format(dateTime);
  }

  static String formatDate(String? isoString) {
    final dateTime = parseIsoString(isoString);
    if (dateTime == null) return '--/--/----';
    return _dateFormat.format(dateTime);
  }

  static String formatDateTime(String? isoString) {
    final dateTime = parseIsoString(isoString);
    if (dateTime == null) return '--/--/---- --:--:--';
    return _dateTimeFormat.format(dateTime);
  }

  static double calculateWorkHours(String? checkIn, String? checkOut) {
    final checkInTime = parseIsoString(checkIn);
    final checkOutTime = parseIsoString(checkOut);

    if (checkInTime == null || checkOutTime == null) return 0.0;

    final duration = checkOutTime.difference(checkInTime);
    return duration.inMinutes / 60.0;
  }

  static String getCurrentTime() {
    return _timeFormat.format(DateTime.now());
  }

  static String getCurrentDate() {
    return _dateFormat.format(DateTime.now());
  }
}
