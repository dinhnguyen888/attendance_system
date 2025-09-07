#pragma once

#include "base_screen.hpp"

class LoadingScreen : public BaseScreen {
private:
    AppState next_state;
    
public:
    LoadingScreen();
    bool Show() override;
    AppState GetNextState() const override;
};
