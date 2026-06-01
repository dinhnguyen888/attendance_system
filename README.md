# Face Attendance System

Face Attendance System is an Odoo-based attendance project with face login and employee face registration. Odoo stores employee and attendance data, while a separate Python gRPC service analyzes images and short webcam videos with InsightFace, OpenCV, ONNX Runtime, and YOLO-based anti-spoofing checks.

## Services

- `odoo`: Odoo 18 with the `face_attendance` custom addon.
- `postgres`: PostgreSQL database for Odoo.
- `face_ai_solver`: Python gRPC service for face registration and verification.

## Main Features

- Face login from the Odoo login page.
- Automatic check-in after successful face verification.
- Face embedding registration from employee profile images.
- Configurable similarity threshold, valid frame count, video size limit, and spoofing tolerance.
- Optional company-level IP allow/block lists for face attendance.

## Requirements

- Docker
- Docker Compose
- A webcam-enabled browser for face login

## Quick Start

```bash
docker compose up -d --build
```

Open Odoo at:

```text
http://localhost:8069
```

Default database settings are defined in `odoo.conf` and `docker-compose.yml`.

## Default Access

```text
Username: admin
Password: admin
```

## Test Environment Credentials

```text
URL: http://localhost:8069
Database: odoo_db
Username: admin
Password: admin
```

On a fresh database, Docker Compose initializes the Odoo base schema and installs the `RESP Face Attendance` addon automatically.

## Configuration

In Odoo, go to **Settings > Face Attendance** and review:

- `AI gRPC Target`: defaults to `face_ai_solver:50051` when running with Docker Compose.
- `Default Similarity Threshold`
- `Minimum Valid Frames`
- `Maximum Spoofing Error Rate`
- `Maximum Video Size (MB)`
- Optional IP restrictions

For local non-Docker development, set the gRPC target to:

```text
localhost:50051
```

## How to Use

1. Go to **Apps**.
2. Search for the `face_attendance` module.
3. Activate the module.
4. Go to **Employees** and update the employee face image.
5. Log out of Odoo.
6. On the login page, click **Face Login**.
7. After a successful scan, Odoo opens automatically and the Attendance module creates a new check-in record if the employee does not already have an open attendance record for the day.

## Useful Commands

Start all services:

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f
```

Stop all services:

```bash
docker compose down
```

Reset containers and volumes:

```bash
docker compose down -v
```

## Project Structure

```text
.
+-- custom_addons/
|   +-- Dockerfile
|   +-- face_attendance/
+-- face_ai_solver/
|   +-- Dockerfile
|   +-- app/
|   +-- main.py
|   +-- requirements.txt
+-- docker-compose.yml
+-- odoo.conf
+-- README.md
```

## Notes

- The AI solver exposes gRPC on port `50051`.
- Odoo is exposed on port `8069`.
- PostgreSQL is exposed on port `5432`.
- InsightFace model files are cached in the `face_ai_models` Docker volume.
