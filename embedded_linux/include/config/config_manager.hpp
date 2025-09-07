#pragma once

#include <string>
#include <nlohmann/json.hpp>

class ConfigManager {
private:
    nlohmann::json config;
    std::string config_file_path;
    bool loaded;

public:
    ConfigManager(const std::string& config_path = "config/server_config.json");
    
    bool LoadConfig();
    bool SaveConfig();
    
    // Server configuration
    std::string GetServerUrl() const;
    int GetServerTimeout() const;
    int GetRetryAttempts() const;
    
    // Camera configuration
    int GetCameraDeviceId() const;
    int GetCameraWidth() const;
    int GetCameraHeight() const;
    int GetCameraFps() const;
    
    // Face detection configuration
    std::string GetCascadeFile() const;
    double GetScaleFactor() const;
    int GetMinNeighbors() const;
    int GetMinSize() const;
    
    // Network configuration
    std::string GetWifiIp() const;
    std::string GetDeviceName() const;
    
    // Setters
    void SetServerUrl(const std::string& url);
    void SetWifiIp(const std::string& ip);
    
    bool IsLoaded() const { return loaded; }
};
