# Face Attendance System

Hệ thống điểm danh bằng khuôn mặt tích hợp với Odoo, sử dụng AI và Computer Vision để xác thực khuôn mặt với độ chính xác cao.

## Công nghệ sử dụng

### Backend Technologies
- **Odoo 16+** - ERP framework chính cho quản lý nhân sự và điểm danh
- **Python 3.8+** - Ngôn ngữ lập trình chính
- **PostgreSQL 13** - Cơ sở dữ liệu chính
- **FastAPI 0.104.1** - Web framework cho Face Recognition API
- **Uvicorn** - ASGI server cho FastAPI

### Face Recognition & AI
- **InsightFace 0.7.3** - Thư viện AI nhận diện khuôn mặt tiên tiến
- **OpenCV 4.8.1** - Computer Vision cho xử lý ảnh và video
- **ONNX Runtime 1.18.1** - Runtime cho các mô hình AI
- **NumPy 1.24.3** - Xử lý mảng và tính toán khoa học
- **Scikit-image 0.21.0** - Xử lý ảnh nâng cao

### Frontend Technologies
- **Odoo Web Framework** - Giao diện web tích hợp sẵn trong Odoo
- **HTML5/CSS3/JavaScript** - Frontend templates và static files
- **WebRTC** - Truy cập camera trực tiếp từ trình duyệt
- **Odoo QWeb Templates** - Template engine của Odoo

### Mobile Technologies (Flutter App)
- **Flutter 3.1.0+** - Cross-platform mobile framework
- **Dart** - Ngôn ngữ lập trình cho Flutter
- **Camera Plugin 0.10.5** - Truy cập camera trên mobile
- **HTTP 1.1.0** - HTTP client cho API calls
- **Provider 6.1.1** - State management
- **Shared Preferences 2.2.2** - Local storage
- **Flutter Secure Storage 9.0.0** - Secure data storage
- **Permission Handler 11.0.1** - Quản lý quyền truy cập

### DevOps & Infrastructure
- **Docker & Docker Compose** - Containerization và orchestration
- **Git** - Version control system


### Advanced Features
- **Multiple Face Registration** - Đăng ký nhiều góc chụp
- **Skin Tone Normalization** - Chuẩn hóa màu da
- **Background Validation** - Kiểm tra nền ảnh
- **Face Quality Enhancement** - Tăng chất lượng ảnh khuôn mặt
- **Embedding Diversity Analysis** - Phân tích độ đa dạng đặc trưng
- **Real-time Processing** - Xử lý thời gian thực

## Kiến trúc hệ thống

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Odoo ERP       │    │  Face Recognition│
│   (WebRTC UI)   │───▶│   Controller     │───▶│   API Service   │
│                 │    │   (Python)       │    │   (FastAPI+AI)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐             │
         │              │   PostgreSQL     │             │
         └──────────────│   Database       │─────────────┘
                        │   (Odoo Data)    │
                        └──────────────────┘
                                 │
                        ┌──────────────────┐
                        │   Mobile App     │
                        │   (Flutter)      │
                        │   REST API       │
                        └──────────────────┘
```

## Luồng hoạt động

1. **Nhân viên sử dụng Face Attendance**: Truy cập vào menu "Face Attendance" trong Odoo
2. **Chụp ảnh khuôn mặt**: Nhân viên chụp ảnh khuôn mặt qua webcam
3. **Gửi ảnh về Controller**: Frontend gửi ảnh về Odoo controller
4. **Gọi API Face Recognition**: Controller gọi API service để xác thực khuôn mặt
5. **Xử lý bằng AI**: API service sử dụng InsightFace và OpenCV để:
   - Phát hiện và chuẩn hóa khuôn mặt trong ảnh
   - Trích xuất embedding vector từ khuôn mặt
   - So sánh với các embedding đã lưu (hỗ trợ nhiều ảnh)
   - Áp dụng các bộ lọc chất lượng và validation
   - Trả về kết quả xác thực với confidence score
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
- Phát hiện khuôn mặt sử dụng InsightFace AI models
- Trích xuất embedding vectors với độ chính xác cao
- Hỗ trợ đăng ký nhiều ảnh từ các góc khác nhau
- Chuẩn hóa màu da và tăng chất lượng ảnh
- Kiểm tra nền ảnh và tỷ lệ khung hình (3:4)
- So sánh khuôn mặt với cosine similarity
- Lưu trữ multiple embeddings cho mỗi nhân viên

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




## License

MIT License
