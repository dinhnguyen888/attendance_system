import 'dart:io';
import 'package:flutter/services.dart';

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
        return {
          'ssid': result['ssid']?.toString(),
          'ip': result['ip']?.toString(),
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
        'ip': await _getDeviceIP(),
      };
    }
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
