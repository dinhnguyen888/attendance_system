FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Ho_Chi_Minh

# Build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    git \
    tzdata \
    libboost-all-dev \
    python3-dev python3-numpy \
    libopencv-dev libopencv-contrib-dev \
    libavcodec-dev libavformat-dev libswscale-dev \
    libtbb-dev libjpeg-dev libpng-dev libtiff-dev \
    libcurl4-openssl-dev \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source code (no models/cascade here; mounted via volumes at runtime)
COPY src/ ./src/
COPY CMakeLists.txt ./

# Build
RUN mkdir build && cd build && \
    cmake .. -DUSE_ONNX_RUNTIME=OFF -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc)


# ----- RUNTIME IMAGE -----
FROM ubuntu:24.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Ho_Chi_Minh

# Install runtime libraries and filebrowser
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    libgomp1 \
    libtbb12 \
    libjpeg-turbo8 \
    libpng16-16 \
    libtiff6 \
    libavcodec60 libavformat60 libswscale7 \
    libgtk-3-0 \
    libopencv-dev \
    ffmpeg \
    libcurl4 \
    wget \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

# Install filebrowser
RUN wget --no-check-certificate -O /tmp/filebrowser.tar.gz https://github.com/filebrowser/filebrowser/releases/download/v2.27.0/linux-amd64-filebrowser.tar.gz \
    && tar -xzf /tmp/filebrowser.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/filebrowser \
    && rm /tmp/filebrowser.tar.gz

WORKDIR /app

# Copy entrypoint, binary, and required files
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
COPY --from=builder /app/build/face_3d_match_api /app/face_3d_match_api

# Copy model and cascade files
COPY models/ /app/models/
COPY cascade/ /app/cascade/

# Prepare runtime dirs
RUN mkdir -p /app/employee_data

EXPOSE 8080 8081

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/app/face_3d_match_api", "--model", "models/resnet100.onnx", "--port", "8080"]
