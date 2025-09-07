#pragma once

#include "base_screen.hpp"
#include "api/api_client.hpp"
#include <memory>

class MenuScreen : public BaseScreen {
private:
    AppState next_state;
    std::shared_ptr<ApiClient> api_client;
    std::string selected_action;
    
public:
    MenuScreen();
    bool Show() override;
    AppState GetNextState() const override;
    
    void SetApiClient(std::shared_ptr<ApiClient> client) { api_client = client; }
    std::string GetSelectedAction() const { return selected_action; }
    
private:
    void HandleCheckIn();
    void HandleCheckOut();
    void HandleViewSchedule();
};
