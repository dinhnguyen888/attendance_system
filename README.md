# Face Attendance System

Hệ thống điểm danh bằng khuôn mặt tích hợp với Odoo, sử dụng OpenCV để xác thực khuôn mặt.

## Kiến trúc hệ thống

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Odoo Controller│    │  Face Recognition│
│   (Webcam UI)   │───▶│   (Odoo Addon)   │───▶│   API Service   │
│                 │    │                  │    │   (OpenCV)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Luồng hoạt động

1. **Nhân viên sử dụng Face Attendance**: Truy cập vào menu "Face Attendance" trong Odoo
2. **Chụp ảnh khuôn mặt**: Nhân viên chụp ảnh khuôn mặt qua webcam
3. **Gửi ảnh về Controller**: Frontend gửi ảnh về Odoo controller
4. **Gọi API Face Recognition**: Controller gọi API service để xác thực khuôn mặt
5. **Xử lý bằng OpenCV**: API service sử dụng OpenCV để:
   - Phát hiện khuôn mặt trong ảnh
   - So sánh với ảnh đã lưu (nếu có)
   - Trả về kết quả xác thực
6. **Lưu attendance**: Nếu xác thực thành công, lưu bản ghi attendance vào Odoo

## Cài đặt và chạy

### Yêu cầu hệ thống
- Docker và Docker Compose
- Python 3.8+ (cho development)
- Webcam hỗ trợ

### Chạy bằng Docker Compose

1. **Clone repository**:
```bash
git clone <repository-url>
cd attendance_system
```

2. **Chạy hệ thống**:
```bash
docker-compose up -d
```

3. **Truy cập ứng dụng**:
- Odoo: http://localhost:8069
- Face Recognition API: http://localhost:8000

### Chạy riêng lẻ (Development)

#### 1. Chạy Face Recognition API
```bash
cd custom_api_services
pip install -r requirements.txt
python main.py
```

#### 2. Chạy Odoo
```bash
# Cài đặt Odoo theo hướng dẫn chính thức
# Copy custom_addons vào addons path
# Cấu hình odoo.conf
```

## Cấu hình

### Odoo Configuration (odoo.conf)
```ini
[options]
addons_path = /mnt/extra-addons
data_dir = /var/lib/odoo
admin_passwd = admin
db_host = postgres
db_port = 5432
db_user = odoo
db_password = odoo
```

### API Configuration
- URL: http://localhost:8000 (có thể thay đổi trong controller)
- Port: 8000
- CORS: Đã cấu hình để cho phép Odoo gọi API

## Sử dụng

### 1. Đăng ký khuôn mặt (lần đầu)
- Đăng nhập vào Odoo với tài khoản nhân viên
- Truy cập menu "Face Attendance"
- Chụp ảnh khuôn mặt và nhấn "Register Face"

### 2. Check-in/Check-out hàng ngày
- Truy cập menu "Face Attendance"
- Chụp ảnh khuôn mặt
- Nhấn "Check In" hoặc "Check Out"

## API Endpoints

### Face Recognition API (Port 8000)

#### POST /face-recognition/verify
Xác thực khuôn mặt cho check-in/check-out
```json
{
  "face_image": "base64_image_data",
  "action": "check_in|check_out",
  "employee_id": 123
}
```

#### POST /face-recognition/register
Đăng ký khuôn mặt cho nhân viên mới
```json
{
  "face_image": "base64_image_data"
}
```

#### GET /face-recognition/health
Kiểm tra trạng thái API

### Odoo Controller Endpoints

#### POST /attendance/check_in
Check-in với xác thực khuôn mặt

#### POST /attendance/check_out
Check-out với xác thực khuôn mặt

#### POST /attendance/register_face
Đăng ký khuôn mặt

#### GET /attendance/face_api_health
Kiểm tra trạng thái API face recognition

## Tính năng

### Face Recognition
- Phát hiện khuôn mặt sử dụng Haar Cascade
- Trích xuất đặc trưng sử dụng ORB
- So sánh khuôn mặt với độ chính xác cao
- Lưu trữ ảnh khuôn mặt cho từng nhân viên

### Security
- Xác thực người dùng Odoo
- Kiểm tra session
- Validation dữ liệu đầu vào
- Error handling toàn diện

### User Experience
- Giao diện webcam responsive
- Real-time camera preview
- Hướng dẫn định vị khuôn mặt
- Thông báo kết quả rõ ràng

## Troubleshooting

### API không kết nối được
1. Kiểm tra service face_recognition_api đã chạy chưa
2. Kiểm tra port 8000 có bị block không
3. Kiểm tra URL trong controller có đúng không

### Camera không hoạt động
1. Kiểm tra quyền truy cập camera
2. Kiểm tra webcam có được hỗ trợ không
3. Thử refresh trang

### Face recognition không chính xác
1. Đảm bảo ánh sáng đủ sáng
2. Khuôn mặt phải rõ ràng, không bị che
3. Chỉ có một khuôn mặt trong khung hình

## Development

### Cấu trúc thư mục
```
attendance_system/
├── custom_addons/
│   └── attendance_system/
│       ├── controllers/
│       ├── models/
│       ├── views/
│       └── __manifest__.py
├── custom_api_services/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

### Thêm tính năng mới
1. Cập nhật API service trong `custom_api_services/main.py`
2. Cập nhật controller trong `custom_addons/attendance_system/controllers/`
3. Cập nhật frontend trong `custom_addons/attendance_system/views/`
4. Test và deploy

## License

MIT License
