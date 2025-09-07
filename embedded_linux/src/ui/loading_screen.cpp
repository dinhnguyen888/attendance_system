#include "ui/loading_screen.hpp"
#include "ui/ui_utils.hpp"

LoadingScreen::LoadingScreen() : BaseScreen(), next_state(AppState::LOADING) {
}

bool LoadingScreen::Show() {
    int box_height = 10;
    int box_width = 40;
    int box_y = (LINES - box_height) / 2;
    int box_x = (COLS - box_width) / 2;
    
    UIUtils::DrawBox(box_y, box_x, box_height, box_width);
    
    UIUtils::CenterText(box_y + 2, "DANG XU LY...", 3);
    UIUtils::CenterText(box_y + 4, "Hanh dong: " + loading_action);
    UIUtils::CenterText(box_y + 6, "Nhan Enter de tiep tuc");
    
    int ch = getch();
    
    if (ch == '\n' || ch == '\r') {
        message_text = loading_action + " thanh cong!";
        is_error = false;
        next_state = AppState::MESSAGE;
    }
    
    return true;
}

AppState LoadingScreen::GetNextState() const {
    return next_state;
}
