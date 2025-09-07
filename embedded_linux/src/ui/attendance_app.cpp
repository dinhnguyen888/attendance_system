#include "ui/attendance_app.hpp"
#include "ui/ui_utils.hpp"
#include "ui/login_screen.hpp"
#include "ui/menu_screen.hpp"
#include "ui/loading_screen.hpp"
#include "ui/message_screen.hpp"
#include "ui/schedule_screen.hpp"
#include "ui/camera_screen.hpp"
#include <ncurses.h>
#include <iostream>

AttendanceApp::AttendanceApp() : current_state(AppState::LOGIN) {
    InitializeConfig();
    InitializeApiClient();
    InitializeScreens();
}

AttendanceApp::~AttendanceApp() {
    CleanupNCurses();
}

void AttendanceApp::Run() {
    InitializeNCurses();
    
    while (true) {
        clear();
        
        auto current_screen = screens[current_state];
        if (!current_screen->Show()) {
            break; // Exit application
        }
        
        // Get next state from current screen
        AppState next_state = current_screen->GetNextState();
        
        // Share data between screens when transitioning
        if (next_state != current_state) {
            auto next_screen = screens[next_state];
            
            // Transfer employee ID
            next_screen->SetEmployeeId(current_screen->GetEmployeeId());
            
            // Transfer message and loading action for specific transitions
            if (next_state == AppState::MESSAGE) {
                auto login_screen = std::dynamic_pointer_cast<LoginScreen>(current_screen);
                auto menu_screen = std::dynamic_pointer_cast<MenuScreen>(current_screen);
                auto loading_screen = std::dynamic_pointer_cast<LoadingScreen>(current_screen);
                
                if (login_screen) {
                    next_screen->SetMessage(login_screen->GetEmployeeId().empty() ? 
                        "Vui long nhap ma so nhan vien!" : 
                        (login_screen->GetEmployeeId() == "1" ? "Dang nhap thanh cong!" : "Dang nhap that bai! Ma so nhan vien khong dung!"),
                        login_screen->GetEmployeeId() != "1");
                } else if (loading_screen) {
                    // Get loading action from loading screen and create success message
                    std::string action = "Check In"; // Default, should be passed from loading screen
                    next_screen->SetMessage(action + " thanh cong!", false);
                }
            } else if (next_state == AppState::CAMERA_CAPTURE) {
                auto menu_screen = std::dynamic_pointer_cast<MenuScreen>(current_screen);
                if (menu_screen) {
                    auto camera_screen = std::dynamic_pointer_cast<CameraScreen>(next_screen);
                    if (camera_screen) {
                        camera_screen->SetAction(menu_screen->GetSelectedAction());
                    }
                }
            } else if (next_state == AppState::LOADING) {
                auto menu_screen = std::dynamic_pointer_cast<MenuScreen>(current_screen);
                if (menu_screen) {
                    // Transfer loading action - this would need to be implemented in MenuScreen
                    // For now, we'll handle it in the loading screen itself
                }
            }
            
            current_state = next_state;
        }
        
        refresh();
    }
}

void AttendanceApp::InitializeScreens() {
    auto login_screen = std::make_shared<LoginScreen>();
    login_screen->SetApiClient(api_client);
    screens[AppState::LOGIN] = login_screen;
    
    auto menu_screen = std::make_shared<MenuScreen>();
    menu_screen->SetApiClient(api_client);
    screens[AppState::MENU] = menu_screen;
    
    screens[AppState::LOADING] = std::make_shared<LoadingScreen>();
    screens[AppState::MESSAGE] = std::make_shared<MessageScreen>();
    
    auto schedule_screen = std::make_shared<ScheduleScreen>();
    schedule_screen->SetApiClient(api_client);
    screens[AppState::VIEW_SCHEDULE] = schedule_screen;
    
    auto camera_screen = std::make_shared<CameraScreen>();
    camera_screen->SetApiClient(api_client.get());
    camera_screen->SetConfigManager(config_manager.get());
    screens[AppState::CAMERA_CAPTURE] = camera_screen;
}

void AttendanceApp::InitializeConfig() {
    config_manager = std::make_shared<ConfigManager>();
    if (!config_manager->IsLoaded()) {
        // Handle config loading error - continue with defaults
        std::cerr << "Warning: Using default configuration" << std::endl;
    }
}

void AttendanceApp::InitializeApiClient() {
    std::string server_url = config_manager->GetServerUrl();
    api_client = std::make_shared<ApiClient>(server_url);
}

void AttendanceApp::InitializeNCurses() {
    initscr();
    cbreak();
    noecho();
    keypad(stdscr, TRUE);
    curs_set(0);
    
    UIUtils::InitializeColors();
}

void AttendanceApp::CleanupNCurses() {
    endwin();
}
