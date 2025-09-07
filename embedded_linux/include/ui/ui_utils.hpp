#pragma once

#include <ncurses.h>
#include <string>

class UIUtils {
public:
    static void InitializeColors();
    static void DrawBox(int y, int x, int height, int width);
    static void CenterText(int y, const std::string& text, int color_pair = 0);
};
