# Hướng dẫn sử dụng hệ thống Face Attendance

## Tổng quan

Hệ thống Face Attendance cho phép nhân viên điểm danh bằng khuôn mặt thông qua webcam, tích hợp với Odoo để quản lý attendance.

## Luồng hoạt động

1. **Nhân viên truy cập Face Attendance**: Vào menu "Face Attendance" trong Odoo
2. **Chụp ảnh khuôn mặt**: Sử dụng webcam để chụp ảnh
3. **Xác thực khuôn mặt**: Hệ thống sẽ kiểm tra khuôn mặt bằng OpenCV
4. **Lưu attendance**: Nếu xác thực thành công, lưu bản ghi điểm danh

## Cài đặt và chạy hệ thống

### Bước 1: Cài đặt Docker
```bash
# Tải và cài đặt Docker Desktop từ https://www.docker.com/products/docker-desktop
```

### Bước 2: Clone và chạy dự án
```bash
# Clone repository
git clone <repository-url>
cd attendance_system

# Chạy hệ thống
docker-compose up -d
```

### Bước 3: Truy cập ứng dụng
- **Odoo**: http://localhost:8069
- **Face Recognition API**: http://localhost:8000

### Bước 4: Cài đặt module trong Odoo
1. Đăng nhập Odoo với tài khoản admin
2. Vào Settings → General → Developer Mode (bật ON)
3. Vào Apps → Tìm và cài đặt:
   - Attendances
   - Employees  
   - Attendance System Customized

## Sử dụng hệ thống

### Đăng ký khuôn mặt (lần đầu sử dụng)

1. **Đăng nhập Odoo** với tài khoản nhân viên
2. **Truy cập Face Attendance**: Vào menu "Face Attendance"
3. **Chụp ảnh đăng ký**:
   - Nhấn "Capture" để chụp ảnh
   - Đảm bảo khuôn mặt rõ ràng, ánh sáng tốt
   - Chỉ có một khuôn mặt trong khung hình
4. **Đăng ký**: Nhấn "Register Face" để lưu khuôn mặt

### Check-in hàng ngày

1. **Truy cập Face Attendance**
2. **Chụp ảnh**: Nhấn "Capture" để chụp ảnh khuôn mặt
3. **Check-in**: Nhấn "Check In" để điểm danh vào
4. **Xác nhận**: Hệ thống sẽ hiển thị thông báo thành công

### Check-out hàng ngày

1. **Truy cập Face Attendance**
2. **Chụp ảnh**: Nhấn "Capture" để chụp ảnh khuôn mặt
3. **Check-out**: Nhấn "Check Out" để điểm danh ra
4. **Xác nhận**: Hệ thống sẽ hiển thị thông báo thành công

## Lưu ý quan trọng

### Điều kiện chụp ảnh tốt
- **Ánh sáng**: Đủ sáng, không bị ngược sáng
- **Khuôn mặt**: Rõ ràng, không bị che khuất
- **Khoảng cách**: Vừa phải, không quá gần hoặc quá xa
- **Số lượng**: Chỉ có một khuôn mặt trong khung hình

### Quy tắc điểm danh
- **Check-in**: Chỉ được check-in một lần mỗi ngày
- **Check-out**: Phải check-out sau ít nhất 1 phút từ khi check-in
- **Thời gian**: Hệ thống sử dụng múi giờ của server

### Xử lý lỗi thường gặp

#### Camera không hoạt động
- Kiểm tra quyền truy cập camera trong trình duyệt
- Thử refresh trang
- Kiểm tra webcam có được kết nối không

#### Không nhận diện được khuôn mặt
- Đảm bảo ánh sáng đủ sáng
- Khuôn mặt phải rõ ràng, không bị che
- Thử điều chỉnh góc chụp

#### Lỗi kết nối API
- Kiểm tra service face_recognition_api đã chạy chưa
- Kiểm tra port 8000 có bị block không
- Liên hệ admin để kiểm tra

## Tính năng nâng cao

### Xem lịch sử điểm danh
- Vào menu "Attendances" trong Odoo
- Xem danh sách các lần điểm danh
- Lọc theo nhân viên, ngày tháng

### Quản lý nhân viên
- Vào menu "Employees" trong Odoo
- Thêm/sửa/xóa nhân viên
- Gán tài khoản cho nhân viên

### Báo cáo attendance
- Vào menu "Reporting" → "Attendances"
- Xem báo cáo theo thời gian
- Export dữ liệu ra Excel

## Cấu hình hệ thống

### Thay đổi URL API
Nếu cần thay đổi URL của Face Recognition API:
1. Mở file `custom_addons/attendance_system/controllers/attendance_controller.py`
2. Thay đổi giá trị `FACE_RECOGNITION_API_URL`
3. Restart Odoo service

### Cấu hình độ chính xác
Để thay đổi độ chính xác của face recognition:
1. Mở file `custom_api_services/main.py`
2. Thay đổi giá trị `confidence > 0.6` (dòng 108)
3. Restart API service

## Troubleshooting

### Lỗi "Session expired"
- Đăng nhập lại Odoo
- Kiểm tra session có bị timeout không

### Lỗi "Không tìm thấy nhân viên"
- Kiểm tra tài khoản đăng nhập có được gán employee không
- Liên hệ admin để kiểm tra

### Lỗi "Đã check-in hôm nay"
- Kiểm tra xem đã check-in chưa
- Nếu cần check-out trước khi check-in lại

### Lỗi "Phải check-out sau ít nhất 1 phút"
- Đợi ít nhất 1 phút từ lần check-in
- Hoặc liên hệ admin để reset

## Liên hệ hỗ trợ

Nếu gặp vấn đề không thể tự giải quyết:
1. Ghi lại thông báo lỗi chính xác
2. Chụp màn hình lỗi
3. Liên hệ admin hoặc developer

## Cập nhật hệ thống

Để cập nhật code mới:
```bash
# Pull code mới
git pull

# Restart services
docker-compose down
docker-compose up -d

# Update module Odoo
docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -d odoo_db -u attendance_system --stop-after-init
```
