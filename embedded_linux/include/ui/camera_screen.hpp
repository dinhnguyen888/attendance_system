#pragma once

#include "base_screen.hpp"
#include "../api/api_client.hpp"
#include "../config/config_manager.hpp"
#include "../opencv_wrapper.hpp"
#include <thread>
#include <atomic>

class CameraScreen : public BaseScreen {
private:
    AppState next_state;
    cv::VideoCapture camera;
    cv::Mat captured_image;
    std::thread camera_thread;
    std::atomic<bool> camera_running;
    std::atomic<bool> image_captured;
    std::atomic<bool> show_capture_controls;
    std::atomic<bool> captured_image_ready;
    
    // API and attendance data
    ApiClient* api_client;
    ConfigManager* config_manager;
    std::string current_employee_id;
    std::string action_type;
    
public:
    CameraScreen();
    ~CameraScreen();
    
    bool Show() override;
    AppState GetNextState() const override;
    
    void SetAction(const std::string& action) { action_type = action; }
    void SetApiClient(ApiClient* client) { api_client = client; }
    void SetConfigManager(ConfigManager* config) { config_manager = config; }
    void SetEmployeeId(const std::string& employee_id) { current_employee_id = employee_id; }
    cv::Mat GetCapturedImage() const { return captured_image; }
    
private:
    void InitializeCamera();
    void CameraLoop();
    void CaptureImage();
    void DrawFaceGuide(cv::Mat& frame);
    bool DetectFace(const cv::Mat& frame, cv::Rect& face_rect);
    void ShowCaptureControls();
    void HandleCaptureInput();
    void CleanupCamera();
};
