#include "ui/login_screen.hpp"
#include "ui/ui_utils.hpp"

LoginScreen::LoginScreen() : BaseScreen(), next_state(AppState::LOGIN) {
}

bool LoginScreen::Show() {
    ShowLoginForm();
    return true;
}

void LoginScreen::ShowLoginForm() {
    int box_height = 16;
    int box_width = 60;
    int box_y = (LINES - box_height) / 2;
    int box_x = (COLS - box_width) / 2;
    
    UIUtils::DrawBox(box_y, box_x, box_height, box_width);
    
    UIUtils::CenterText(box_y + 2, "HE THONG CHAM CONG", 4);
    UIUtils::CenterText(box_y + 3, "Embedded Linux Client", 3);
    
    // Hiển thị ô nhập mã số nhân viên
    int input_y = box_y + 6;
    int input_x = box_x + 10;
    int input_width = 30;
    
    mvprintw(input_y - 1, input_x, "Ma so nhan vien:");
    
    // Vẽ khung cho ô nhập
    for (int i = 0; i < input_width; i++) {
        mvaddch(input_y, input_x + i, '_');
    }
    
    // Hiển thị mã số nhân viên đã nhập
    if (!employee_id.empty()) {
        mvprintw(input_y, input_x + 1, "%s", employee_id.c_str());
    }
    
    // Hiển thị cursor
    mvaddch(input_y, input_x + 1 + employee_id.length(), '|');
    
    UIUtils::CenterText(box_y + 9, "[Enter] Dang nhap  [Esc] Thoat");
    UIUtils::CenterText(box_y + 11, "Chi can nhap ma nhan vien", 3);
    
    int ch = getch();
    
    switch (ch) {
        case '\n':
        case '\r':
            if (!employee_id.empty()) {
                // Đăng nhập trực tiếp với mã nhân viên, không cần mật khẩu
                PerformLogin();
            }
            break;
        case 27: // ESC key
        case 'q':
        case 'Q':
            return;
        case KEY_BACKSPACE:
        case 127:
        case 8:
            if (!employee_id.empty()) {
                employee_id.pop_back();
            }
            break;
        default:
            if ((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) {
                if (employee_id.length() < 20) {
                    employee_id += ch;
                }
            }
            break;
    }
}

void LoginScreen::PerformLogin() {
    if (!api_client) {
        SetMessage("Lỗi: API client chưa được khởi tạo", true);
        next_state = AppState::MESSAGE;
        return;
    }
    
    // Đăng nhập chỉ với mã nhân viên, không cần mật khẩu
    ApiResponse response = api_client->Login(employee_id);
    
    if (response.success) {
        SetMessage("Đăng nhập thành công! Chào mừng " + employee_id);
        next_state = AppState::MENU;
    } else {
        SetMessage("Đăng nhập thất bại: " + response.message, true);
        next_state = AppState::MESSAGE;
    }
}

AppState LoginScreen::GetNextState() const {
    return next_state;
}

