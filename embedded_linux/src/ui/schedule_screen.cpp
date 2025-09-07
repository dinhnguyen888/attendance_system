#include "ui/schedule_screen.hpp"
#include "ui/ui_utils.hpp"

ScheduleScreen::ScheduleScreen() : BaseScreen(), next_state(AppState::VIEW_SCHEDULE), data_loaded(false) {
}

bool ScheduleScreen::Show() {
    if (!data_loaded) {
        LoadAttendanceHistory();
    }
    
    DisplayHistory();
    
    int ch = getch();
    
    if (ch == '\n' || ch == '\r' || ch == 27) { // Enter or ESC
        next_state = AppState::MENU;
    } else if (ch == 'r' || ch == 'R') { // Refresh
        data_loaded = false;
        LoadAttendanceHistory();
    }
    
    return true;
}

AppState ScheduleScreen::GetNextState() const {
    return next_state;
}

void ScheduleScreen::LoadAttendanceHistory() {
    if (!api_client) {
        attendance_history.clear();
        data_loaded = true;
        return;
    }
    
    ApiResponse response = api_client->GetAttendanceHistory();
    attendance_history.clear();
    
    if (response.success && response.data.is_array()) {
        for (const auto& record : response.data) {
            AttendanceRecord attendance;
            attendance.date = record.value("date", "");
            attendance.check_in = record.value("check_in", "");
            attendance.check_out = record.value("check_out", "");
            attendance.total_hours = record.value("total_hours", 0.0);
            attendance.status = record.value("status", "");
            
            attendance_history.push_back(attendance);
        }
    }
    
    data_loaded = true;
}

void ScheduleScreen::DisplayHistory() {
    int box_height = LINES - 4;
    int box_width = COLS - 4;
    int box_y = 2;
    int box_x = 2;
    
    UIUtils::DrawBox(box_y, box_x, box_height, box_width);
    
    UIUtils::CenterText(box_y + 1, "LICH SU CHAM CONG", 4);
    UIUtils::CenterText(box_y + 2, "Nhan vien: " + employee_id, 3);
    
    if (attendance_history.empty()) {
        UIUtils::CenterText(box_y + 5, "Khong co du lieu lich cham cong", 2);
    } else {
        // Header
        mvprintw(box_y + 4, box_x + 2, "%-12s %-10s %-10s %-8s %-10s", 
                "Ngay", "Vao", "Ra", "Gio", "Trang thai");
        mvprintw(box_y + 5, box_x + 2, "%-12s %-10s %-10s %-8s %-10s", 
                "------------", "----------", "----------", "--------", "----------");
        
        // Data rows
        int row = 0;
        int max_rows = box_height - 10;
        
        for (const auto& record : attendance_history) {
            if (row >= max_rows) break;
            
            int y = box_y + 6 + row;
            
            // Format date
            std::string formatted_date = record.date.substr(5); // Remove year, show MM-DD
            
            // Format times
            std::string check_in_time = record.check_in.empty() ? "--:--" : record.check_in.substr(11, 5);
            std::string check_out_time = record.check_out.empty() ? "--:--" : record.check_out.substr(11, 5);
            
            // Format hours
            std::string hours_str = record.total_hours > 0 ? 
                std::to_string(static_cast<int>(record.total_hours)) + "h" + 
                std::to_string(static_cast<int>((record.total_hours - static_cast<int>(record.total_hours)) * 60)) + "m" : 
                "--";
            
            // Status color
            int color = 0;
            if (record.status == "completed") color = 1; // Green
            else if (record.status == "working") color = 3; // Yellow
            
            if (color > 0) attron(COLOR_PAIR(color));
            mvprintw(y, box_x + 2, "%-12s %-10s %-10s %-8s %-10s", 
                    formatted_date.c_str(),
                    check_in_time.c_str(),
                    check_out_time.c_str(),
                    hours_str.c_str(),
                    record.status.c_str());
            if (color > 0) attroff(COLOR_PAIR(color));
            
            row++;
        }
    }
    
    UIUtils::CenterText(box_y + box_height - 3, "[Enter] Quay lai  [R] Tai lai");
    UIUtils::CenterText(box_y + box_height - 2, "[Esc] Thoat");
}
