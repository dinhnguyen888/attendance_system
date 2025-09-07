#pragma once

#include "app_state.hpp"
#include "../api/api_client.hpp"
#include "../config/config_manager.hpp"
#include "base_screen.hpp"
#include <map>
#include <memory>

class AttendanceApp {
private:
    AppState current_state;
    std::map<AppState, std::shared_ptr<BaseScreen>> screens;
    std::shared_ptr<ApiClient> api_client;
    std::shared_ptr<ConfigManager> config_manager;

public:
    AttendanceApp();
    ~AttendanceApp();
    
    void Run();
    
private:
    void InitializeScreens();
    void InitializeApiClient();
    void InitializeConfig();
    void InitializeNCurses();
    void CleanupNCurses();
};
