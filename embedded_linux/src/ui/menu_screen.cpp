#include "ui/menu_screen.hpp"
#include "ui/ui_utils.hpp"

MenuScreen::MenuScreen() : BaseScreen(), next_state(AppState::MENU) {
}

bool MenuScreen::Show() {
    int box_height = 14;
    int box_width = 40;
    int box_y = (LINES - box_height) / 2;
    int box_x = (COLS - box_width) / 2;
    
    UIUtils::DrawBox(box_y, box_x, box_height, box_width);
    
    UIUtils::CenterText(box_y + 2, "MENU CHAM CONG", 4);
    UIUtils::CenterText(box_y + 3, "Nhan vien: " + employee_id);
    
    std::string options[] = {"Check In", "Check Out", "Xem lich cham cong", "Quay lai"};
    
    for (int i = 0; i < 4; i++) {
        int y = box_y + 5 + i * 2;
        std::string display = "[" + std::to_string(i + 1) + "] " + options[i];
        UIUtils::CenterText(y, display);
    }
    
    int ch = getch();
    
    switch (ch) {
        case '1':
            HandleCheckIn();
            break;
        case '2':
            HandleCheckOut();
            break;
        case '3':
            HandleViewSchedule();
            break;
        case '4':
        case 'q':
        case 'Q':
            next_state = AppState::LOGIN;
            employee_id = "";
            break;
    }
    
    return true;
}

AppState MenuScreen::GetNextState() const {
    return next_state;
}

void MenuScreen::HandleCheckIn() {
    selected_action = "check_in";
    loading_action = "Check In";
    next_state = AppState::CAMERA_CAPTURE;
}

void MenuScreen::HandleCheckOut() {
    selected_action = "check_out";
    loading_action = "Check Out";
    next_state = AppState::CAMERA_CAPTURE;
}

void MenuScreen::HandleViewSchedule() {
    next_state = AppState::VIEW_SCHEDULE;
}
