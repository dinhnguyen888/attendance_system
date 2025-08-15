# 📋 Hướng Dẫn Sử Dụng Hệ Thống Face Attendance

## 🎯 Tổng Quan

Hệ thống Face Attendance là một module Odoo tùy chỉnh cho phép nhân viên chấm công bằng cách chụp ảnh khuôn mặt thông qua webcam. Hệ thống tích hợp với module `hr.attendance` có sẵn của Odoo.

## 🏗️ Kiến Trúc Hệ Thống

### 📁 Cấu Trúc Thư Mục

```
attendance_system/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── attendance_controller.py
├── models/
│   ├── __init__.py
│   └── attendance.py
├── security/
│   └── ir.model.access.csv
├── views/
│   ├── attendance_view.xml
│   └── webcam_template.xml
└── tools/
    └── camera_client.py
```

### 🔧 Các Thành Phần Chính

#### 1. **Models** (`models/attendance.py`)

- Mở rộng model `hr.attendance` có sẵn
- Thêm trường `face_image` để lưu ảnh khuôn mặt

#### 2. **Controllers** (`controllers/attendance_controller.py`)

- Xử lý các request HTTP/JSON
- Logic check-in/check-out với validation
- Quản lý session và authentication

#### 3. **Views** (`views/`)

- `attendance_view.xml`: Menu và form view
- `webcam_template.xml`: Giao diện webcam

## 🔄 Logic Hoạt Động

### 📸 Quy Trình Check-in

#### 1. **Validation Trước Check-in**

```python
# Kiểm tra session user
if not request.env.user or not request.env.user.id:
    return {'error': 'Session expired. Vui lòng đăng nhập lại.'}

# Kiểm tra employee_id
employee_id = request.env.user.employee_id.id
if not employee_id:
    return {'error': 'Không tìm thấy nhân viên'}

# Kiểm tra ảnh khuôn mặt
face_image = kw.get('face_image')
if not face_image:
    return {'error': 'Không có ảnh khuôn mặt'}
```

#### 2. **Kiểm Tra Trạng Thái Hiện Tại**

```python
# Kiểm tra có bản ghi chưa check-out không
existing_attendance = request.env['hr.attendance'].sudo().search([
    ('employee_id', '=', employee_id),
    ('check_out', '=', False)
], limit=1)

if existing_attendance:
    return {'error': 'Bạn đã check-in. Vui lòng check-out trước.'}
```

#### 3. **Kiểm Tra Check-in Trong Ngày**

```python
# Tính toán thời gian trong ngày
current_time = fields.Datetime.now()
start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
end_of_day = start_of_day + timedelta(days=1)

# Kiểm tra đã check-in hôm nay chưa
today_attendance = request.env['hr.attendance'].sudo().search([
    ('employee_id', '=', employee_id),
    ('check_in', '>=', start_of_day),
    ('check_in', '<', end_of_day)
])

if today_attendance:
    return {'error': 'Bạn đã check-in hôm nay. Vui lòng check-out trước.'}
```

#### 4. **Tạo Bản Ghi Check-in**

```python
attendance = request.env['hr.attendance'].sudo().create({
    'employee_id': employee_id,
    'face_image': face_image,
})
```

### 🚪 Quy Trình Check-out

#### 1. **Validation Tương Tự Check-in**

- Kiểm tra session
- Kiểm tra employee_id
- Kiểm tra ảnh khuôn mặt

#### 2. **Tìm Bản Ghi Check-in**

```python
attendance = request.env['hr.attendance'].sudo().search([
    ('employee_id', '=', employee_id),
    ('check_out', '=', False)
], limit=1, order='check_in desc')

if not attendance:
    return {'error': 'Không tìm thấy bản ghi check-in để check-out'}
```

#### 3. **Kiểm Tra Thời Gian Tối Thiểu**

```python
current_time = fields.Datetime.now()
check_in_time = attendance.check_in

if check_in_time and (current_time - check_in_time).total_seconds() < 60:
    return {'error': 'Phải check-out sau ít nhất 1 phút từ khi check-in'}
```

#### 4. **Cập Nhật Check-out**

```python
attendance.write({
    'check_out': current_time,
    'face_image': face_image,
})
```

## 🛡️ Business Rules & Validation

### ✅ Các Quy Tắc Đã Implement

#### 1. **Ngăn Check-in Nhiều Lần**

- Không cho phép check-in khi chưa check-out
- Một nhân viên chỉ được check-in 1 lần/ngày

#### 2. **Kiểm Tra Thời Gian**

- Check-out phải sau ít nhất 1 phút từ check-in
- Tính toán chính xác thời gian trong ngày

#### 3. **Validation Dữ Liệu**

- Kiểm tra session user hợp lệ
- Kiểm tra employee_id tồn tại
- Kiểm tra ảnh khuôn mặt được cung cấp

### ❌ Các Hạn Chế Hiện Tại

#### 1. **Không Có Face Recognition**

- Chỉ lưu ảnh, không xác minh danh tính
- Không so sánh khuôn mặt với database

#### 2. **Không Có Time-based Rules**

- Không kiểm tra giờ làm việc
- Không tính overtime
- Không có late/early rules

## 🎨 Giao Diện Người Dùng

### 📱 Webcam Interface

#### **Layout:**

- **Header**: Tiêu đề và hướng dẫn
- **Camera**: Video stream với face guide hình tròn
- **Buttons**: Capture, Check In, Check Out
- **Result**: Hiển thị kết quả/thông báo lỗi

#### **Responsive Design:**

- Tối ưu cho desktop và mobile
- Kích thước tự động điều chỉnh
- Vừa một màn hình không cần scroll

### 🔘 Các Nút Chức Năng

#### 1. **Capture Button**

- Chụp ảnh từ webcam
- Chuyển sang chế độ xem ảnh
- Có thể chụp lại

#### 2. **Check In Button**

- Chỉ active sau khi chụp ảnh
- Gửi request check-in
- Hiển thị loading state

#### 3. **Check Out Button**

- Chỉ active sau khi chụp ảnh
- Gửi request check-out
- Hiển thị loading state

## 🚀 Cài Đặt & Chạy

### 📋 Yêu Cầu Hệ Thống

- Docker & Docker Compose
- Odoo 17.0
- PostgreSQL 15
- Webcam hỗ trợ

### 🔧 Cài Đặt

#### 1. **Clone Repository**

```bash
git clone <repository_url>
cd attendance_system
```

#### 2. **Khởi Động Docker**

```bash
docker-compose up -d
```

#### 3. **Cập Nhật Module**

```bash
docker exec -it attendance_system-odoo-1 bash -c "odoo -c /etc/odoo/odoo.conf -d odoo_db -u attendance_system --stop-after-init"
```

### 🌐 Truy Cập Hệ Thống

- **URL**: `http://localhost:8069`
- **Username**: `admin`
- **Password**: `admin`

## 📊 Quản Lý Dữ Liệu

### 📈 Xem Báo Cáo Attendance

1. Vào menu **Attendance > Face Attendance**
2. Xem danh sách các bản ghi chấm công
3. Mỗi bản ghi có ảnh khuôn mặt đính kèm

### 🔍 Tìm Kiếm & Lọc

- Lọc theo nhân viên
- Lọc theo ngày
- Tìm kiếm theo thời gian

## 🛠️ Troubleshooting

### ❌ Lỗi Thường Gặp

#### 1. **Camera Access Denied**

- **Nguyên nhân**: Browser không cho phép truy cập camera
- **Giải pháp**: Cho phép camera trong browser settings

#### 2. **Session Expired**

- **Nguyên nhân**: Phiên đăng nhập hết hạn
- **Giải pháp**: Đăng nhập lại Odoo

#### 3. **Không Tìm Thấy Nhân Viên**

- **Nguyên nhân**: User không liên kết với employee
- **Giải pháp**: Tạo employee record cho user

#### 4. **Check-in/Check-out Lỗi**

- **Nguyên nhân**: Vi phạm business rules
- **Giải pháp**: Kiểm tra thông báo lỗi và làm theo hướng dẫn

### 🔧 Maintenance Commands

#### **Restart Odoo**

```bash
docker restart attendance_system-odoo-1
```

#### **Update Module**

```bash
docker exec -it attendance_system-odoo-1 bash -c "odoo -c /etc/odoo/odoo.conf -d odoo_db -u attendance_system --stop-after-init"
```

#### **View Logs**

```bash
docker logs attendance_system-odoo-1
```

## 🔮 Tính Năng Tương Lai

### 🎯 Có Thể Phát Triển Thêm

#### 1. **Face Recognition**

- Xác minh danh tính người dùng
- So sánh khuôn mặt với database
- Confidence score

#### 2. **Advanced Time Rules**

- Giờ làm việc linh hoạt
- Tính overtime
- Late/early detection

#### 3. **Mobile App**

- Ứng dụng mobile native
- Push notifications
- Offline support

#### 4. **Analytics & Reporting**

- Dashboard thống kê
- Báo cáo chi tiết
- Export data

## 📞 Hỗ Trợ

### 👥 Team Phát Triển

- **Đỉnh**: Backend & Database
- **Huy**: Frontend & UI/UX
- **Khánh**: System Integration

### 📧 Liên Hệ

- **Email**: [team_email]
- **GitHub**: [repository_url]
- **Documentation**: [docs_url]

---

_Cập nhật lần cuối: 15/08/2025_
