import 'dart:io';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

class WiFiService {
  static final WiFiService _instance = WiFiService._internal();
  factory WiFiService() => _instance;
  WiFiService._internal();

  static const MethodChannel _channel = MethodChannel('wifi_info');

  Future<Map<String, String?>> getWiFiInfo() async {
    try {
      if (Platform.isAndroid) {
        // Trên Android, thử lấy thông tin WiFi qua platform channel
        final Map<dynamic, dynamic> result =
            await _channel.invokeMethod('getWiFiInfo');

        // Ưu tiên: Public IPv4 của mạng (WAN IP) -> Gateway WiFi -> IP cục bộ
        final publicIp = await _getPublicIPv4();
        final gatewayIp = result['ip']?.toString();

        return {
          'ssid': result['ssid']?.toString(),
          'ip': publicIp ?? gatewayIp ?? await _getDeviceIP(),
        };
      } else {
        // Fallback cho các platform khác
        return {
          'ssid': 'Unknown',
          'ip': await _getDeviceIP(),
        };
      }
    } catch (e) {
      print('Error getting WiFi info: $e');
      // Fallback: lấy IP từ network interface
      return {
        'ssid': 'Unknown',
        'ip': await _getPublicIPv4() ?? await _getDeviceIP(),
      };
    }
  }

  Future<String?> _getPublicIPv4() async {
    try {
      // Thử api.ipify trước
      final r1 = await http
          .get(Uri.parse('https://api.ipify.org?format=text'))
          .timeout(const Duration(seconds: 5));
      if (r1.statusCode == 200) {
        final ip = r1.body.trim();
        if (_isValidIPv4(ip)) return ip;
      }
    } catch (_) {}
    try {
      // Fallback icanhazip
      final r2 = await http
          .get(Uri.parse('https://ipv4.icanhazip.com'))
          .timeout(const Duration(seconds: 5));
      if (r2.statusCode == 200) {
        final ip = r2.body.trim();
        if (_isValidIPv4(ip)) return ip;
      }
    } catch (_) {}
    return null;
  }

  bool _isValidIPv4(String ip) {
    final regex = RegExp(
        r'^((25[0-5]|2[0-4]\d|[0-1]?\d?\d)\.){3}(25[0-5]|2[0-4]\d|[0-1]?\d?\d)$');
    return regex.hasMatch(ip);
  }

  Future<String?> _getDeviceIP() async {
    try {
      // Lấy IP từ network interfaces
      for (var interface in await NetworkInterface.list()) {
        for (var addr in interface.addresses) {
          if (addr.type == InternetAddressType.IPv4 && !addr.isLoopback) {
            // Ưu tiên IP trong dải private (WiFi thường là 192.168.x.x)
            if (addr.address.startsWith('192.168.') ||
                addr.address.startsWith('10.') ||
                addr.address.startsWith('172.')) {
              return addr.address;
            }
          }
        }
      }
      return null;
    } catch (e) {
      print('Error getting device IP: $e');
      return null;
    }
  }

  Future<String?> getWiFiSSID() async {
    final info = await getWiFiInfo();
    return info['ssid'];
  }

  Future<String?> getWiFiIP() async {
    final info = await getWiFiInfo();
    return info['ip'];
  }
}
