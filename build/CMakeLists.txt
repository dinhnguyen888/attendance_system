cmake_minimum_required(VERSION 3.16)
project(AttendanceClient LANGUAGES CXX)

# -----------------------------
# Compiler setup
# -----------------------------
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if (CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
elseif (MSVC)
    add_compile_options(/W4 /permissive- /EHsc)
endif()

# -----------------------------
# Dependencies
# -----------------------------
find_package(Boost REQUIRED COMPONENTS system thread)
find_package(OpenCV REQUIRED)
find_package(CURL REQUIRED)

# JSON lib
find_package(nlohmann_json 3.2.0 QUIET)
if (NOT nlohmann_json_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        nlohmann_json
        URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz
    )
    FetchContent_MakeAvailable(nlohmann_json)
endif()

# FTXUI (TUI lib)
include(FetchContent)
FetchContent_Declare(
    ftxui
    GIT_REPOSITORY https://github.com/ftxui/ftxui.git
    GIT_TAG v5.0.0   # đổi sang version ổn định mới nhất nếu cần
)
FetchContent_MakeAvailable(ftxui)

# -----------------------------
# Target
# -----------------------------
add_executable(attendance_client
    sources/main.cpp
    sources/camera.cpp
    sources/http_client.cpp
    sources/tui.cpp
)

target_include_directories(attendance_client
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${Boost_INCLUDE_DIRS}
)

target_link_libraries(attendance_client
    PRIVATE
        Boost::system
        Boost::thread
        CURL::libcurl
        ${OpenCV_LIBS}
        nlohmann_json::nlohmann_json
        ftxui::screen
        ftxui::dom
        ftxui::component
)

# -----------------------------
# Installation (optional)
# -----------------------------
install(TARGETS attendance_client RUNTIME DESTINATION bin)
