#include "ui/camera_screen.hpp"
#include "ui/ui_utils.hpp"
#include <chrono>
#include <thread>
#include <cstdio>

CameraScreen::CameraScreen() : BaseScreen(), next_state(AppState::MENU), 
    camera_running(false), image_captured(false), show_capture_controls(false), 
    captured_image_ready(false), api_client(nullptr), config_manager(nullptr) {
}

CameraScreen::~CameraScreen() {
    CleanupCamera();
}

bool CameraScreen::Show() {
    if (!camera_running) {
        InitializeCamera();
    }
    
    if (show_capture_controls) {
        ShowCaptureControls();
        return true;
    }
    
    // Hiển thị giao diện camera trong terminal
    int box_height = 15;
    int box_width = 60;
    int box_y = (LINES - box_height) / 2;
    int box_x = (COLS - box_width) / 2;
    
    UIUtils::DrawBox(box_y, box_x, box_height, box_width);
    
    UIUtils::CenterText(box_y + 2, "CAMERA CHAM CONG", 4);
    UIUtils::CenterText(box_y + 4, "Hanh dong: " + loading_action);
    
    if (camera_running) {
        UIUtils::CenterText(box_y + 6, "Camera dang hoat dong...", 1);
        UIUtils::CenterText(box_y + 7, "Dat khuon mat vao vung ellipse");
        UIUtils::CenterText(box_y + 9, "[Space] Chup anh");
        UIUtils::CenterText(box_y + 10, "[Esc] Huy bo");
    } else {
        UIUtils::CenterText(box_y + 6, "Khong the mo camera!", 2);
        UIUtils::CenterText(box_y + 8, "[Enter] Thu lai");
        UIUtils::CenterText(box_y + 9, "[Esc] Quay lai");
    }
    
    int ch = getch();
    
    switch (ch) {
        case ' ': // Space - chụp ảnh
            if (camera_running) {
                CaptureImage();
            }
            break;
        case '\n':
        case '\r':
            if (!camera_running) {
                InitializeCamera();
            }
            break;
        case 27: // ESC
        case 'q':
        case 'Q':
            CleanupCamera();
            next_state = AppState::MENU;
            break;
    }
    
    return true;
}

AppState CameraScreen::GetNextState() const {
    return next_state;
}

void CameraScreen::InitializeCamera() {
    if (!camera.isOpened()) {
        // Get camera settings from config
        int device_id = config_manager ? config_manager->GetCameraDeviceId() : 0;
        int width = config_manager ? config_manager->GetCameraWidth() : 640;
        int height = config_manager ? config_manager->GetCameraHeight() : 480;
        int fps = config_manager ? config_manager->GetCameraFps() : 30;
        
        camera.open(device_id);
        if (!camera.isOpened()) {
            clear();
            attron(COLOR_PAIR(2)); // Red
            mvprintw(LINES/2 - 1, (COLS - 35)/2, "ERROR: Cannot open camera device %d", device_id);
            attroff(COLOR_PAIR(2));
            mvprintw(LINES/2 + 1, (COLS - 40)/2, "Please check camera connection and permissions");
            mvprintw(LINES/2 + 3, (COLS - 30)/2, "Press any key to return to menu...");
            refresh();
            getch();
            next_state = AppState::MENU;
            return;
        }
        
        // Set camera properties with error checking
        if (!camera.set(cv::CAP_PROP_FRAME_WIDTH, width)) {
            mvprintw(1, 2, "Warning: Could not set camera width to %d", width);
        }
        if (!camera.set(cv::CAP_PROP_FRAME_HEIGHT, height)) {
            mvprintw(2, 2, "Warning: Could not set camera height to %d", height);
        }
        if (!camera.set(cv::CAP_PROP_FPS, fps)) {
            mvprintw(3, 2, "Warning: Could not set camera FPS to %d", fps);
        }
        
        refresh();
    }
    camera_running = true;
    camera_thread = std::thread(&CameraScreen::CameraLoop, this);
}

void CameraScreen::CameraLoop() {
    cv::Mat frame;
    cv::CascadeClassifier face_cascade;
    
    // Load face cascade classifier from config
    std::string cascade_file = config_manager ? config_manager->GetCascadeFile() : 
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_alt.xml";
    
    if (!face_cascade.load(cascade_file)) {
        // Try fallback paths
        if (!face_cascade.load("haarcascade_frontalface_alt.xml") &&
            !face_cascade.load("/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml")) {
            // Face detection will be disabled
        }
    }
    
    while (camera_running && camera.isOpened()) {
        camera >> frame;
        if (frame.empty()) continue;
        
        // Flip frame horizontally (mirror effect)
        cv::flip(frame, frame, 1);
        
        // Draw face guide ellipse
        DrawFaceGuide(frame);
        
        // Detect faces
        cv::Rect face_rect;
        if (DetectFace(frame, face_rect)) {
            // Draw rectangle around detected face
            cv::rectangle(frame, face_rect, cv::Scalar(0, 255, 0), 2);
        }
        
        // For embedded system, we don't show OpenCV windows
        // Instead, we rely on terminal UI for user interaction
        // cv::imshow("Attendance Camera", frame);
        
        // Check for capture trigger from terminal UI
        if (image_captured) {
            CaptureImage();
            image_captured = false;
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(30));
    }
    
    // cv::destroyAllWindows(); // Not needed for embedded system
}

void CameraScreen::CaptureImage() {
    if (!camera.isOpened()) return;
    
    cv::Mat frame;
    camera >> frame;
    if (!frame.empty()) {
        cv::flip(frame, frame, 1);
        captured_image = frame.clone();
        image_captured = true;
        show_capture_controls = true;
        
        // Pause camera display
        camera_running = false;
        if (camera_thread.joinable()) {
            camera_thread.join();
        }
    }
}

void CameraScreen::DrawFaceGuide(cv::Mat& frame) {
    int center_x = frame.cols / 2;
    int center_y = frame.rows / 2;
    int ellipse_width = 200;
    int ellipse_height = 250;
    
    // Draw ellipse guide
    cv::ellipse(frame, 
                cv::Point(center_x, center_y),
                cv::Size(ellipse_width/2, ellipse_height/2),
                0, 0, 360,
                cv::Scalar(255, 255, 0), 3);
    
    // Add instruction text
    cv::putText(frame, "Dat khuon mat vao day", 
                cv::Point(center_x - 100, center_y + ellipse_height/2 + 30),
                cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(255, 255, 255), 2);
}

bool CameraScreen::DetectFace(const cv::Mat& frame, cv::Rect& face_rect) {
    cv::CascadeClassifier face_cascade;
    
    // Load cascade file from config
    std::string cascade_file = config_manager ? config_manager->GetCascadeFile() : 
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_alt.xml";
    
    if (!face_cascade.load(cascade_file)) {
        // Try fallback paths
        if (!face_cascade.load("haarcascade_frontalface_alt.xml") &&
            !face_cascade.load("/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml")) {
            return false;
        }
    }
    
    cv::Mat gray;
    cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
    
    // Get detection parameters from config
    double scale_factor = config_manager ? config_manager->GetScaleFactor() : 1.1;
    int min_neighbors = config_manager ? config_manager->GetMinNeighbors() : 3;
    int min_size = config_manager ? config_manager->GetMinSize() : 30;
    
    std::vector<cv::Rect> faces;
    face_cascade.detectMultiScale(gray, faces, scale_factor, min_neighbors, 0, 
                                 cv::Size(min_size, min_size));
    
    if (!faces.empty()) {
        face_rect = faces[0]; // Use the first detected face
        return true;
    }
    
    return false;
}

void CameraScreen::ShowCaptureControls() {
    int box_height = 12;
    int box_width = 50;
    int box_y = (LINES - box_height) / 2;
    int box_x = (COLS - box_width) / 2;
    
    UIUtils::DrawBox(box_y, box_x, box_height, box_width);
    
    UIUtils::CenterText(box_y + 2, "HINH ANH DA CHUP", 4);
    UIUtils::CenterText(box_y + 4, "Chon hanh dong:");
    UIUtils::CenterText(box_y + 6, "[1] Chup anh");
    UIUtils::CenterText(box_y + 7, "[2] Chup lai");
    UIUtils::CenterText(box_y + 8, "[3] Xac nhan");
    UIUtils::CenterText(box_y + 9, "[Esc] Huy bo");
    
    int ch = getch();
    
    switch (ch) {
        case '1':
            // Chụp ảnh mới
            show_capture_controls = false;
            camera_running = true;
            camera_thread = std::thread(&CameraScreen::CameraLoop, this);
            break;
        case '2':
            // Chụp lại
            show_capture_controls = false;
            camera_running = true;
            camera_thread = std::thread(&CameraScreen::CameraLoop, this);
            break;
        case '3': // Confirm and proceed
            if (captured_image_ready) {
                mvprintw(LINES - 3, 2, "Processing attendance...");
                refresh();
                
                // Save captured image to temporary file
                std::string temp_filename = "/tmp/attendance_capture.jpg";
                if (cv::imwrite(temp_filename, captured_image)) {
                    // Call API client for attendance processing
                    bool success = false;
                    std::string message;
                    
                    if (api_client && !current_employee_id.empty()) {
                        if (action_type == "check_in") {
                            auto result = api_client->CheckIn(current_employee_id, temp_filename);
                            success = result.success;
                            message = result.message;
                        } else if (action_type == "check_out") {
                            auto result = api_client->CheckOut(current_employee_id, temp_filename);
                            success = result.success;
                            message = result.message;
                        }
                    }
                    
                    // Clean up temp file
                    std::remove(temp_filename.c_str());
                    
                    // Show result
                    clear();
                    if (success) {
                        attron(COLOR_PAIR(3)); // Green
                        mvprintw(LINES/2 - 2, (COLS - 20)/2, "ATTENDANCE SUCCESS");
                        attroff(COLOR_PAIR(3));
                        mvprintw(LINES/2, (COLS - message.length())/2, "%s", message.c_str());
                    } else {
                        attron(COLOR_PAIR(2)); // Red
                        mvprintw(LINES/2 - 2, (COLS - 18)/2, "ATTENDANCE FAILED");
                        attroff(COLOR_PAIR(2));
                        mvprintw(LINES/2, (COLS - message.length())/2, "%s", message.c_str());
                    }
                    
                    mvprintw(LINES - 2, (COLS - 30)/2, "Press any key to continue...");
                    refresh();
                    getch();
                } else {
                    mvprintw(LINES - 3, 2, "Error saving image! Press any key to continue...");
                    refresh();
                    getch();
                }
                
                next_state = AppState::MENU;
                return;
            }
            break;
        case 27: // ESC
            CleanupCamera();
            next_state = AppState::MENU;
            break;
    }
}

void CameraScreen::CleanupCamera() {
    camera_running = false;
    
    if (camera_thread.joinable()) {
        camera_thread.join();
    }
    
    if (camera.isOpened()) {
        camera.release();
    }
    
    // Remove OpenCV window operations for embedded system
    // cv::destroyAllWindows();
}
