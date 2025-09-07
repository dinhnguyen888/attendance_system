#pragma once

#include "base_screen.hpp"
#include "api/api_client.hpp"
#include <memory>

class LoginScreen : public BaseScreen {
private:
    AppState next_state;
    std::shared_ptr<ApiClient> api_client;
    
public:
    LoginScreen();
    bool Show() override;
    AppState GetNextState() const override;
    
    void SetApiClient(std::shared_ptr<ApiClient> client) { api_client = client; }
    
private:
    void PerformLogin();
    void ShowLoginForm();
};
