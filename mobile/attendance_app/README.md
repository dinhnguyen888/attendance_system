# AttendanceFace - Hệ Thống Chấm Công Thông Minh

Ứng dụng di động chấm công tích hợp với Odoo, sử dụng công nghệ nhận diện khuôn mặt để xác thực người dùng.

## 🚀 Tính năng chính

- **🔐 Đăng nhập thông minh**: Tích hợp với Odoo, xác thực người dùng an toàn
- **📱 Chấm công bằng camera**: Check-in/Check-out với nhận diện khuôn mặt
- **🔍 Xác thực khuôn mặt**: Tích hợp với Face Recognition API của Odoo
- **📊 Lịch sử chấm công**: Xem và quản lý lịch sử chấm công chi tiết
- **📍 Định vị GPS**: Ghi nhận vị trí chấm công chính xác
- **📈 Thống kê**: Báo cáo giờ làm việc và hiệu suất
- **🎨 Giao diện MVVM**: Kiến trúc chuẩn, dễ bảo trì và mở rộng

## 🆕 Chức năng Check-in/Check-out mới

### **Tích hợp với API Odoo**

- **Face Verification**: Xác thực khuôn mặt trước khi chấm công
- **Odoo Integration**: Tạo attendance record trực tiếp trong Odoo
- **Real-time Sync**: Đồng bộ dữ liệu ngay lập tức với Odoo server

### **⚠️ Lưu ý quan trọng**

**Chức năng face verification hiện tại cần được setup trước khi sử dụng:**

1. **Face Recognition API Service** phải đang chạy trên port 8000
2. **Employee faces** phải được đăng ký trước trong hệ thống
3. **Odoo Server** phải có module `attendance_system` được cài đặt

**Xem file `FACE_VERIFICATION_GUIDE.md` để biết chi tiết setup.**

### **Quy trình chấm công**

1. **Chụp ảnh**: Sử dụng camera trước để chụp khuôn mặt
2. **Xác thực**: Gửi ảnh đến Face Recognition API để xác thực
3. **Tạo record**: Tạo attendance record trong Odoo với thông tin xác thực
4. **Cập nhật UI**: Refresh dữ liệu và hiển thị thông báo thành công

### **API Endpoints sử dụng**

- **Face Verification**: `/face-recognition/verify` (FastAPI Service)
- **Attendance Creation**: `/web/dataset/call_kw/hr.attendance/create` (Odoo)
- **Mobile APIs**: `/mobile/*` cho các chức năng khác

## 🛠️ Công nghệ sử dụng

- **Frontend**: Flutter 3.x
- **State Management**: Provider (MVVM pattern)
- **Backend**: Odoo ERP System
- **Authentication**: JWT Token + Session Management
- **Database**: Local Storage + Secure Storage
- **Camera**: Face Recognition API tích hợp với Odoo
- **Network**: HTTP/HTTPS với timeout handling

## 📱 Yêu cầu hệ thống

- **Android**: API Level 21+ (Android 5.0+)
- **iOS**: iOS 11.0+
- **Flutter**: 3.1.0+
- **Dart**: 3.1.0+
- **Odoo Server**: 16.0+ với module attendance_system

## 🚀 Cài đặt và chạy

### 1. Cài đặt dependencies

```bash
flutter pub get
```

### 2. Cấu hình Odoo server

Chỉnh sửa file `lib/constants/app_constants.dart`:

```dart
static const String baseUrl = 'http://YOUR_ODOO_IP:8069';
```

### 3. Cấu hình icon app

File cấu hình: `flutter_launcher_icons.yaml`

- Icon chính: `assets/icons/iconAPP.png`
- Tự động tạo icon cho tất cả platform

### 4. Chạy ứng dụng

```bash
flutter run
```

## 🏗️ Cấu trúc dự án

```
lib/
├── constants/          # Hằng số và cấu hình
│   ├── app_constants.dart    # API endpoints, timeout
│   └── app_colors.dart       # Màu sắc giao diện
├── models/            # Data models
│   ├── auth.dart             # Authentication models
│   ├── employee.dart         # Employee information
│   └── attendance.dart       # Attendance records
├── providers/         # State management (MVVM)
│   ├── auth_provider.dart    # Authentication state
│   └── attendance_provider.dart # Attendance state
├── services/          # Business logic và API
│   ├── api_service.dart      # Odoo API integration
│   └── storage_service.dart  # Local data storage
├── views/            # UI screens
│   ├── login_view.dart       # Màn hình đăng nhập
│   ├── home_view.dart        # Màn hình chính
│   └── camera_view.dart      # Màn hình camera chấm công
└── widgets/          # Reusable components
    ├── custom_button.dart     # Button tùy chỉnh
    └── custom_text_field.dart # Input field tùy chỉnh
```

## 🔌 Tích hợp Odoo

### **API Endpoints**

- **Authentication**: `/mobile/auth/login`
- **Profile**: `/mobile/employee/profile`
- **Attendance**: `/mobile/attendance/*`
- **Face Verification**: `/attendance/face_verification`
- **Odoo Web API**: `/web/dataset/call_kw/*`

### **Quyền cần thiết**

- **Camera**: Chụp ảnh chấm công và nhận diện khuôn mặt
- **Storage**: Lưu trữ ảnh và dữ liệu local
- **Location**: GPS để ghi nhận vị trí chấm công
- **Internet**: Kết nối với Odoo server
- **Network State**: Kiểm tra trạng thái mạng

## 🔐 Xác thực và bảo mật

- **JWT Token**: Xác thực API calls
- **Secure Storage**: Lưu trữ token an toàn
- **Session Management**: Quản lý phiên đăng nhập
- **Face Recognition**: Xác thực khuôn mặt trước khi chấm công
- **Error Handling**: Xử lý lỗi chi tiết và thông báo người dùng

## 📱 Giao diện người dùng

### **Màn hình đăng nhập**

- Logo app với thiết kế facial recognition
- Form đăng nhập với validation
- Hiển thị lỗi rõ ràng và thân thiện
- Loading state và error handling

### **Màn hình chính**

- Dashboard chấm công
- Lịch sử chấm công
- Thống kê giờ làm việc
- Cài đặt và profile

### **Màn hình camera**

- Camera trước với khung hướng dẫn ellipse
- Chụp ảnh khuôn mặt
- Xác thực real-time
- Thông báo kết quả xác thực

## 🚨 Xử lý lỗi

### **Các loại lỗi được xử lý**

- **Validation**: Username/password trống
- **Network**: Không thể kết nối server
- **Authentication**: Sai thông tin đăng nhập
- **Face Recognition**: Xác thực khuôn mặt thất bại
- **Server**: Lỗi server (500, 404, 401)
- **Timeout**: Kết nối bị timeout

### **Thông báo lỗi**

- UI thân thiện với màu sắc phù hợp
- Icon lỗi và nút đóng
- Tự động ẩn khi không có lỗi
- Thông báo thành công khi chấm công

## 🔧 Cấu hình Android

### **AndroidManifest.xml**

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
```

### **Network Security**

- `network_security_config.xml`: Cho phép HTTP traffic
- `usesCleartextTraffic="true"`: Hỗ trợ kết nối HTTP

## 📦 Build và Deploy

### **Tạo icon app**

```bash
flutter pub run flutter_launcher_icons:main
```

### **Build APK**

```bash
flutter build apk --release
```

### **Build App Bundle**

```bash
flutter build appbundle --release
```

## 🧪 Testing

### **Test cases**

- Đăng nhập với tài khoản hợp lệ
- Đăng nhập với tài khoản không hợp lệ
- Test lỗi mạng
- Test timeout
- Test validation
- Test face recognition
- Test attendance creation

### **Debug mode**

- Logging chi tiết trong console
- Error tracking và reporting
- Network request monitoring
- Face recognition API testing

## 📈 Roadmap

- [x] Push notifications
- [x] Offline mode
- [x] Multi-language support
- [x] Advanced analytics
- [x] Integration với Odoo
- [x] Face recognition integration
- [ ] Biometric authentication
- [ ] Advanced reporting
- [ ] Team management features

## 🤝 Đóng góp

1. Fork project
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📄 License

Project này được phát hành dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## 📞 Liên hệ

- **Project**: AttendanceFace
- **Version**: 1.0.0
- **Maintainer**: Development Team
- **Email**: support@attendanceface.com

---

**AttendanceFace** - Giải pháp chấm công thông minh cho doanh nghiệp hiện đại 🚀
