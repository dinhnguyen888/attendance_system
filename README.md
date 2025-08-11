# Hướng dẫn cài đặt và chạy dự án

## 1. Cài đặt Docker Desktop

1. Truy cập [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Tải phiên bản phù hợp với hệ điều hành của bạn
3. Cài đặt Docker Desktop
4. Khởi động Docker Desktop
5. Kiểm tra cài đặt bằng lệnh:

```bash
docker --version
```

## 2. Chạy dự án

1. Mở Terminal/Command Prompt
2. Di chuyển đến thư mục dự án
3. Khởi chạy docker compose:

```bash
docker-compose up -d
```

## 3. Truy cập ứng dụng

-   Odoo sẽ chạy tại: http://localhost:8069
-   Đăng nhập với tài khoản mặc định:
    -   Username: admin
    -   Password: admin
