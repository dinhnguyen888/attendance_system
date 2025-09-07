#include "config/config_manager.hpp"
#include <fstream>
#include <iostream>

ConfigManager::ConfigManager(const std::string& config_path) 
    : config_file_path(config_path), loaded(false) {
    LoadConfig();
}

bool ConfigManager::LoadConfig() {
    try {
        std::ifstream file(config_file_path);
        if (!file.is_open()) {
            std::cerr << "Warning: Could not open config file: " << config_file_path << std::endl;
            std::cerr << "Using default configuration values." << std::endl;
            
            // Set default values
            config = {
                {"server", {
                    {"url", "http://localhost:8069"},
                    {"timeout", 30},
                    {"retry_attempts", 3}
                }},
                {"camera", {
                    {"device_id", 0},
                    {"width", 640},
                    {"height", 480},
                    {"fps", 30}
                }},
                {"face_detection", {
                    {"cascade_file", "/usr/share/opencv4/haarcascades/haarcascade_frontalface_alt.xml"},
                    {"scale_factor", 1.1},
                    {"min_neighbors", 3},
                    {"min_size", 30}
                }},
                {"network", {
                    {"wifi_ip", "192.168.1.100"},
                    {"device_name", "embedded_attendance_device"}
                }}
            };
            loaded = true;
            return true;
        }
        
        file >> config;
        loaded = true;
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "Error loading config: " << e.what() << std::endl;
        loaded = false;
        return false;
    }
}

bool ConfigManager::SaveConfig() {
    try {
        std::ofstream file(config_file_path);
        if (!file.is_open()) {
            return false;
        }
        
        file << config.dump(4);
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "Error saving config: " << e.what() << std::endl;
        return false;
    }
}

// Server configuration
std::string ConfigManager::GetServerUrl() const {
    return config.value("server", nlohmann::json{}).value("url", "http://localhost:8069");
}

int ConfigManager::GetServerTimeout() const {
    return config.value("server", nlohmann::json{}).value("timeout", 30);
}

int ConfigManager::GetRetryAttempts() const {
    return config.value("server", nlohmann::json{}).value("retry_attempts", 3);
}

// Camera configuration
int ConfigManager::GetCameraDeviceId() const {
    return config.value("camera", nlohmann::json{}).value("device_id", 0);
}

int ConfigManager::GetCameraWidth() const {
    return config.value("camera", nlohmann::json{}).value("width", 640);
}

int ConfigManager::GetCameraHeight() const {
    return config.value("camera", nlohmann::json{}).value("height", 480);
}

int ConfigManager::GetCameraFps() const {
    return config.value("camera", nlohmann::json{}).value("fps", 30);
}

// Face detection configuration
std::string ConfigManager::GetCascadeFile() const {
    return config.value("face_detection", nlohmann::json{}).value("cascade_file", 
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_alt.xml");
}

double ConfigManager::GetScaleFactor() const {
    return config.value("face_detection", nlohmann::json{}).value("scale_factor", 1.1);
}

int ConfigManager::GetMinNeighbors() const {
    return config.value("face_detection", nlohmann::json{}).value("min_neighbors", 3);
}

int ConfigManager::GetMinSize() const {
    return config.value("face_detection", nlohmann::json{}).value("min_size", 30);
}

// Network configuration
std::string ConfigManager::GetWifiIp() const {
    return config.value("network", nlohmann::json{}).value("wifi_ip", "192.168.1.100");
}

std::string ConfigManager::GetDeviceName() const {
    return config.value("network", nlohmann::json{}).value("device_name", "embedded_attendance_device");
}

// Setters
void ConfigManager::SetServerUrl(const std::string& url) {
    config["server"]["url"] = url;
}

void ConfigManager::SetWifiIp(const std::string& ip) {
    config["network"]["wifi_ip"] = ip;
}
