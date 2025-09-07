#pragma once

#include <ncurses.h>
#include <string>
#include "app_state.hpp"

class BaseScreen {
protected:
    std::string employee_id;
    std::string message_text;
    bool is_error;
    std::string loading_action;

public:
    BaseScreen();
    virtual ~BaseScreen() = default;
    
    virtual bool Show() = 0;
    virtual AppState GetNextState() const = 0;
    
    // Getters and setters
    void SetEmployeeId(const std::string& id) { employee_id = id; }
    std::string GetEmployeeId() const { return employee_id; }
    
    void SetMessage(const std::string& msg, bool error = false) { 
        message_text = msg; 
        is_error = error; 
    }
    
    void SetLoadingAction(const std::string& action) { loading_action = action; }
};
