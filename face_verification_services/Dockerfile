FROM python:3.9

# Cài đặt các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libstdc++6 \
    libxrender1 \
    libgl1 \
    libgomp1 \
    libomp-dev \
    libprotobuf-dev \
    protobuf-compiler \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

# Cài numpy trước để tránh xung đột
RUN pip install numpy==1.24.3

# Cài cả onnxruntime CPU + GPU (InsightFace sẽ tự chọn)
# Chỉ cài onnxruntime CPU. GPU wheel gây lỗi khi không có CUDA
RUN python -m pip install onnxruntime==1.18.1

# Cài insightface và các gói còn lại
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/employee_faces
RUN mkdir -p /app/employee_canny_features
RUN mkdir -p /app/employee_embeddings

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/face-recognition/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
