package com.attendance.app.attendance_app

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.net.InetAddress
import java.nio.ByteBuffer
import java.nio.ByteOrder

class MainActivity : FlutterActivity() {
    private val CHANNEL = "wifi_info"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "getWiFiInfo" -> {
                    try {
                        val info = getWifiInfo()
                        result.success(mapOf("ssid" to info.first, "ip" to info.second))
                    } catch (e: Exception) {
                        result.error("WIFI_ERROR", e.message, null)
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun getWifiInfo(): Pair<String?, String?> {
        val context = applicationContext
        val wifiManager = context.getSystemService(Context.WIFI_SERVICE) as WifiManager
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

        // SSID detection (may require location enabled on Android 10+)
        var ssid: String? = null
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val network = connectivityManager.activeNetwork
                val nc = connectivityManager.getNetworkCapabilities(network)
                if (nc != null && nc.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
                    val wifiInfo = wifiManager.connectionInfo
                    ssid = wifiInfo?.ssid?.replace("\"", "")
                }
            } else {
                ssid = wifiManager.connectionInfo?.ssid?.replace("\"", "")
            }
        } catch (_: Exception) { }

        // Get gateway IPv4 (router IP) from DHCP info
        val gatewayInt = try { wifiManager.dhcpInfo?.gateway ?: 0 } catch (e: Exception) { 0 }
        val gatewayIp = if (gatewayInt != 0) intToIp(gatewayInt) else null

        return Pair(ssid, gatewayIp)
    }

    private fun intToIp(ip: Int): String {
        val buffer = ByteBuffer.allocate(4)
        buffer.order(ByteOrder.LITTLE_ENDIAN)
        buffer.putInt(ip)
        buffer.flip()
        val bytes = ByteArray(4)
        buffer.get(bytes)
        return try {
            InetAddress.getByAddress(bytes).hostAddress
        } catch (e: Exception) {
            ""
        }
    }
}
