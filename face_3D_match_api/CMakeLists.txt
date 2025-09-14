cmake_minimum_required(VERSION 3.16)
project(face_3d_match_api)

set(CMAKE_CXX_STANDARD 17)

find_package(OpenCV REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(CURL REQUIRED libcurl)

include_directories(${OpenCV_INCLUDE_DIRS})
include_directories(${CURL_INCLUDE_DIRS})

include(FetchContent)
FetchContent_Declare(
    crow
    GIT_REPOSITORY https://github.com/CrowCpp/Crow.git
    GIT_TAG v1.0+5
)
FetchContent_MakeAvailable(crow)

set(SOURCES
    src/main.cpp
    src/server.cpp
    src/video_processing.cpp
    src/face_processing.cpp
    src/embeddings.cpp
    src/files.cpp
    src/utils.cpp
    src/http_client.cpp
    src/face_detector.cpp
    src/face_alignment.cpp
    src/arcface_processor.cpp
)

add_executable(${PROJECT_NAME} ${SOURCES})
target_include_directories(${PROJECT_NAME} PRIVATE src ${OpenCV_INCLUDE_DIRS} ${CURL_INCLUDE_DIRS})
target_link_libraries(${PROJECT_NAME} PRIVATE ${OpenCV_LIBS} Crow::Crow ${CURL_LIBRARIES})
