# DFD (Data Flow Diagram) - Face 3D Match API

## 📋 Tổng quan hệ thống

Hệ thống **Face 3D Match API** xử lý 3 chức năng chính: **Register**, **Check-in**, **Check-out**

### 🏗️ **Cấu trúc hệ thống:**
- **Language**: C++17 + OpenCV 4.5+ + Crow framework
- **AI Models**: ResNet100 (ONNX) + Haar Cascade
- **Storage**: File system theo Employee ID
- **Deployment**: Docker Ubuntu 24.04

### 🎯 **3 API Endpoints:**
1. **POST /api/3d-face-register** - Đăng ký khuôn mặt (10 frames)
2. **POST /api/checkin** - Check-in (1 frame + so sánh)
3. **POST /api/checkout** - Check-out (1 frame + so sánh)

### 📁 **Storage Structure:**
```
/app/employee_data/
├── video/employee_{id}/input.mp4
├── image/employee_{id}/frame_0-9.jpg
├── image_preprocess/employee_{id}/pre_0-9.jpg
├── embedding/employee_{id}/emb_0-9.txt + mean.txt
└── comparison/employee_{id}/checkin_*.jpg + checkout_*.jpg
```

## 🔄 Luồng xử lý chính (Main System Flow)

```mermaid
flowchart TD
    A[Client<br/>📱] -->|Request| B{API Endpoint}
    B -->|Register| C[3D Face Register<br/>📝]
    B -->|Check-in| D[Check-in<br/>⏰]
    B -->|Check-out| E[Check-out<br/>🚪]
    
    C --> F[Video Validation<br/>✅]
    D --> F
    E --> F
    
    F --> G[Frame Extraction<br/>🎬]
    G --> H[Face Processing<br/>🔧]
    H --> I[Embedding<br/>🧠]
    
    I --> J{Action Type}
    J -->|Register| K[Save All Data<br/>💾]
    J -->|Check-in/out| L[Compare + Save<br/>🔍]
    
    K --> M[Success Response<br/>✅]
    L --> M
    M --> A
```

## 🔍 Luồng xử lý chi tiết (Detailed Process Flow)

### 📝 **Register Flow:**
```mermaid
flowchart TD
    A[Register Request] --> B[Validate Video]
    B --> C[Extract 10 Frames]
    C --> D[Preprocess Faces]
    D --> E[Compute Embeddings]
    E --> F[Save All Data]
    F --> G[Return Success]
```

### ⏰ **Check-in/out Flow:**
```mermaid
flowchart TD
    A[Check-in/out Request] --> B[Validate Video]
    B --> C[Extract 1 Frame]
    C --> D[Preprocess Face]
    D --> E[Compute Embedding]
    E --> F[Load Stored Embeddings]
    F --> G[Compare Similarity]
    G --> H[Save Comparison Image]
    H --> I[Return Result]
```

## 🏗️ Kiến trúc hệ thống (System Architecture)

```mermaid
graph TB
    subgraph "Client Layer"
        MOBILE[Mobile App<br/>📱]
        WEB[Web App<br/>💻]
    end
    
    subgraph "API Layer"
        REG[Register API<br/>📝]
        IN[Check-in API<br/>⏰]
        OUT[Check-out API<br/>🚪]
    end
    
    subgraph "Processing Layer"
        VALID[Video Validation<br/>✅]
        EXTRACT[Frame Extraction<br/>🎬]
        PREP[Face Processing<br/>🔧]
        AI[AI Processing<br/>🧠]
        COMP[Comparison<br/>🔍]
    end
    
    subgraph "Storage Layer"
        VIDEO[Video Storage<br/>📹]
        FRAMES[Frame Storage<br/>📸]
        EMBEDDINGS[Embedding Storage<br/>🧠]
        COMPARISON[Comparison Storage<br/>🔍]
    end
    
    MOBILE --> REG
    MOBILE --> IN
    MOBILE --> OUT
    WEB --> REG
    WEB --> IN
    WEB --> OUT
    
    REG --> VALID
    IN --> VALID
    OUT --> VALID
    
    VALID --> EXTRACT
    EXTRACT --> PREP
    PREP --> AI
    AI --> COMP
    
    AI --> VIDEO
    AI --> FRAMES
    AI --> EMBEDDINGS
    COMP --> COMPARISON
```

## 📊 Data Flow Summary

```mermaid
flowchart LR
    subgraph "Input"
        I1[Video File<br/>📹]
        I2[Employee ID<br/>👤]
        I3[Action Type<br/>⚡]
    end
    
    subgraph "Processing"
        P1[Face Detection<br/>👁️]
        P2[Image Enhancement<br/>✨]
        P3[Feature Extraction<br/>🧠]
        P4[Comparison<br/>🔍]
    end
    
    subgraph "Output"
        O1[Register Data<br/>📊]
        O2[Check Result<br/>📈]
        O3[Response<br/>✅]
    end
    
    I1 --> P1
    I2 --> P1
    I3 --> P4
    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> O1
    P4 --> O2
    O1 --> O3
    O2 --> O3
```

## 🧩 Key Components

```mermaid
mindmap
  root((Face 3D Match API))
    Input
      Video Upload
      Employee ID
      Action Type
    Processing
      Video Validation
      Frame Extraction
      Face Detection
      Image Enhancement
      Embedding Computation
      Face Comparison
    Storage
      Video Files
      Raw Frames
      Preprocessed Images
      Embedding Vectors
      Comparison Images
    AI Models
      Haar Cascade
      OpenCV DNN
      ResNet100
    Output
      Register Response
      Check-in/out Result
      Error Messages
```

## ⚠️ Error Handling Flow

```mermaid
flowchart TD
    START([Request]) --> VALIDATE{Valid Input?}
    VALIDATE -->|No| ERR1[Missing Data Error]
    VALIDATE -->|Yes| CHECK_VIDEO{Valid Video?}
    CHECK_VIDEO -->|No| ERR2[Video Validation Error]
    CHECK_VIDEO -->|Yes| EXTRACT_FRAMES{Extract Frames?}
    EXTRACT_FRAMES -->|Failed| ERR3[Frame Extraction Error]
    EXTRACT_FRAMES -->|Success| PROCESS{Process Faces?}
    PROCESS -->|Failed| ERR4[Processing Error]
    PROCESS -->|Success| COMPUTE{Compute Embeddings?}
    COMPUTE -->|Failed| ERR5[AI Model Error]
    COMPUTE -->|Success| COMPARE{Compare Faces?}
    COMPARE -->|Failed| ERR6[Comparison Error]
    COMPARE -->|Success| SUCCESS[Success Response]
    
    ERR1 --> END([End])
    ERR2 --> END
    ERR3 --> END
    ERR4 --> END
    ERR5 --> END
    ERR6 --> END
    SUCCESS --> END
```

## 📈 Performance & Optimization

```mermaid
graph LR
    A[Input Video] --> B[Parallel Processing]
    B --> C[Memory Management]
    C --> D[Model Caching]
    D --> E[File Cleanup]
    E --> F[Optimized Output]
    
    subgraph "Optimizations"
        G[Parallel Frame Processing]
        H[Efficient Memory Usage]
        I[Model Reuse]
        J[Automatic Cleanup]
    end
    
    B --> G
    C --> H
    D --> I
    E --> J
```

### ⚡ **Technical Specs:**
- **Video Format**: MP4, AVI, WebM
- **Frame Size**: 112x112 pixels
- **Embedding Dimension**: Dynamic
- **Processing Time**: 2-5 seconds
- **Storage**: ~50MB per employee
- **Similarity Threshold**: 75%

## 🔧 Deployment

```mermaid
graph TB
    A[Docker Build] --> B[Container Image]
    B --> C[Volume Mounts]
    C --> D[API Server]
    
    subgraph "Volumes"
        E[models/]
        F[cascade/]
        G[employee_data/]
    end
    
    C --> E
    C --> F
    C --> G
    D --> H[Port 8080]
```

### 🐳 **Docker Commands:**
```bash
# Build
docker build -t face-3d-api .

# Run
docker run -p 8080:8080 \
  -v ./models:/app/models \
  -v ./cascade:/app/cascade \
  -v ./employee_data:/app/employee_data \
  face-3d-api
```

### 🌐 **API Endpoints:**
- `GET /api/health` - Health check
- `POST /api/3d-face-register` - Register face
- `POST /api/checkin` - Check-in
- `POST /api/checkout` - Check-out
