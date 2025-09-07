#pragma once

#include "base_screen.hpp"
#include "../api/api_client.hpp"
#include <memory>
#include <vector>
#include <string>

class ScheduleScreen : public BaseScreen {
private:
    AppState next_state;
    std::shared_ptr<ApiClient> api_client;
    std::vector<AttendanceRecord> attendance_history;
    bool data_loaded;
    
public:
    ScheduleScreen();
    bool Show() override;
    AppState GetNextState() const override;
    
    void SetApiClient(std::shared_ptr<ApiClient> client) { api_client = client; }
    
private:
    void LoadAttendanceHistory();
    void DisplayHistory();
};
