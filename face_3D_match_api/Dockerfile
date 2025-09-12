FROM ubuntu:24.04

# Avoid tzdata interactive prompt
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Ho_Chi_Minh

# Install dependencies (OpenCV 4.8+ có sẵn trong repo Noble)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    wget \
    curl \
    git \
    unzip \
    libgomp1 \
    tzdata \
    libboost-all-dev \
    python3-dev python3-numpy \
    libopencv-dev libopencv-contrib-dev \
    libgtk-3-dev \
    libavcodec-dev libavformat-dev libswscale-dev \
    libtbb-dev libtbbmalloc2 libjpeg-dev libpng-dev libtiff-dev \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------
# Build your application
# ---------------------------
WORKDIR /app
ENV LD_LIBRARY_PATH=/app/build/_deps/onnxruntime-src/lib:$LD_LIBRARY_PATH

# Copy source code and cascade files
COPY src/ ./src/
COPY CMakeLists.txt ./
COPY models/ ./models/
COPY cascade/ ./cascade/

# Add entrypoint script
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create build directory and build
RUN mkdir build && cd build && \
    cmake .. -DUSE_ONNX_RUNTIME=OFF && \
    make -j$(nproc)

# Create data directory for employee embeddings
RUN mkdir -p employee_data

# Expose port
EXPOSE 8080

# Default command
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["./build/face_3d_match_api", "--model", "models/resnet100.onnx", "--port", "8080"]
