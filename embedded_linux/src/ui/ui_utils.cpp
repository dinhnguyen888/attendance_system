#include "ui/ui_utils.hpp"

void UIUtils::InitializeColors() {
    if (has_colors()) {
        start_color();
        init_pair(1, COLOR_GREEN, COLOR_BLACK);
        init_pair(2, COLOR_RED, COLOR_BLACK);
        init_pair(3, COLOR_YELLOW, COLOR_BLACK);
        init_pair(4, COLOR_CYAN, COLOR_BLACK);
    }
}

void UIUtils::DrawBox(int y, int x, int height, int width) {
    for (int i = 0; i < height; i++) {
        for (int j = 0; j < width; j++) {
            if (i == 0 || i == height - 1) {
                mvaddch(y + i, x + j, '-');
            } else if (j == 0 || j == width - 1) {
                mvaddch(y + i, x + j, '|');
            } else {
                mvaddch(y + i, x + j, ' ');
            }
        }
    }
    mvaddch(y, x, '+');
    mvaddch(y, x + width - 1, '+');
    mvaddch(y + height - 1, x, '+');
    mvaddch(y + height - 1, x + width - 1, '+');
}

void UIUtils::CenterText(int y, const std::string& text, int color_pair) {
    int x = (COLS - text.length()) / 2;
    if (color_pair > 0) attron(COLOR_PAIR(color_pair));
    mvprintw(y, x, "%s", text.c_str());
    if (color_pair > 0) attroff(COLOR_PAIR(color_pair));
}
