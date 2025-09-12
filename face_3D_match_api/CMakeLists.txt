cmake_minimum_required(VERSION 3.16)
project(face_3d_match_api)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Find OpenCV
find_package(OpenCV 4.5 REQUIRED)

# Optional: ONNX Runtime
option(USE_ONNX_RUNTIME "Use ONNX Runtime" ON)
if(USE_ONNX_RUNTIME)
    include(FetchContent)
    FetchContent_Declare(
        onnxruntime
        URL https://github.com/microsoft/onnxruntime/releases/download/v1.16.3/onnxruntime-linux-x64-1.16.3.tgz
    )
    FetchContent_MakeAvailable(onnxruntime)
    include_directories(${onnxruntime_SOURCE_DIR}/include)
    link_directories(${onnxruntime_SOURCE_DIR}/lib)
    add_definitions(-DUSE_ONNX_RUNTIME)
endif()

# Optional: Crow
include(FetchContent)
FetchContent_Declare(
    crow
    GIT_REPOSITORY https://github.com/CrowCpp/Crow.git
    GIT_TAG v1.0+5
)
FetchContent_MakeAvailable(crow)

# Download ArcFace model if not exists
set(ARCFACE_MODEL_PATH "${CMAKE_SOURCE_DIR}/models/arcface_r100.onnx")
if(NOT EXISTS ${ARCFACE_MODEL_PATH})
    message(STATUS "Downloading ArcFace R100 model...")
    file(MAKE_DIRECTORY "${CMAKE_SOURCE_DIR}/models")
    # Prefer media.githubusercontent.com which serves LFS content directly
    file(DOWNLOAD 
        "https://media.githubusercontent.com/media/onnx/models/main/vision/body_analysis/arcface/model/arcface_r100.onnx"
        ${ARCFACE_MODEL_PATH}
        SHOW_PROGRESS
        TIMEOUT 300
        STATUS DOWNLOAD_STATUS
    )
    list(GET DOWNLOAD_STATUS 0 DOWNLOAD_CODE)
    if(NOT DOWNLOAD_CODE EQUAL 0)
        message(WARNING "Primary download failed, trying fallback URL...")
        file(DOWNLOAD 
            "https://github.com/onnx/models/raw/main/vision/body_analysis/arcface/model/arcface_r100.onnx?download=1"
            ${ARCFACE_MODEL_PATH}
            SHOW_PROGRESS
            TIMEOUT 300
        )
    endif()
    if(EXISTS ${ARCFACE_MODEL_PATH})
        file(SIZE ${ARCFACE_MODEL_PATH} MODEL_SIZE)
        if(MODEL_SIZE LESS 5000000)
            message(WARNING "Downloaded model seems too small (${MODEL_SIZE}). It may be an HTML page. Please provide the model manually.")
        else()
            message(STATUS "ArcFace model downloaded successfully (${MODEL_SIZE} bytes)")
        endif()
    else()
        message(WARNING "Failed to download ArcFace model. Please download manually.")
    endif()
endif()

# Sources
set(SOURCES
    src/main.cpp
    src/face_detector.cpp
    src/face_recognizer.cpp
    src/arcface_model.cpp
    src/api_server.cpp
    src/utils.cpp
)

# Executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Linking
target_include_directories(${PROJECT_NAME} PRIVATE src ${OpenCV_INCLUDE_DIRS})
target_link_libraries(${PROJECT_NAME} PRIVATE ${OpenCV_LIBS} Crow::Crow)

if(USE_ONNX_RUNTIME)
    target_link_libraries(${PROJECT_NAME} PRIVATE onnxruntime)
endif()
