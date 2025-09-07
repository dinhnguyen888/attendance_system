#pragma once

#include "base_screen.hpp"

class MessageScreen : public BaseScreen {
private:
    AppState next_state;
    
public:
    MessageScreen();
    bool Show() override;
    AppState GetNextState() const override;
};
