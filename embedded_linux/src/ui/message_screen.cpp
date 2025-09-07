#include "ui/message_screen.hpp"
#include "ui/ui_utils.hpp"

MessageScreen::MessageScreen() : BaseScreen(), next_state(AppState::MESSAGE) {
}

bool MessageScreen::Show() {
    int box_height = 10;
    int box_width = 60;
    int box_y = (LINES - box_height) / 2;
    int box_x = (COLS - box_width) / 2;
    
    UIUtils::DrawBox(box_y, box_x, box_height, box_width);
    
    UIUtils::CenterText(box_y + 2, "THONG BAO", 4);
    UIUtils::CenterText(box_y + 4, message_text, is_error ? 2 : 1);
    UIUtils::CenterText(box_y + 6, "[Enter] OK");
    
    int ch = getch();
    
    if (ch == '\n' || ch == '\r') {
        if (!is_error && message_text.find("Dang nhap thanh cong") != std::string::npos) {
            next_state = AppState::MENU;
        } else if (is_error && (message_text.find("Dang nhap that bai") != std::string::npos || 
                               message_text.find("Vui long nhap") != std::string::npos)) {
            next_state = AppState::LOGIN;
        } else {
            next_state = AppState::MENU;
        }
    }
    
    return true;
}

AppState MessageScreen::GetNextState() const {
    return next_state;
}
