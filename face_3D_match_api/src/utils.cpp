#include "utils.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <algorithm>
#include <chrono>
#include <iomanip>
#include <filesystem>

namespace Utils {

bool fileExists(const std::string& path) {
    return std::filesystem::exists(path);
}

std::vector<uint8_t> readBinaryFile(const std::string& path) {
    std::vector<uint8_t> data;
    
    try {
        std::ifstream file(path, std::ios::binary | std::ios::ate);
        if (!file.is_open()) {
            return data;
        }
        
        std::streamsize size = file.tellg();
        file.seekg(0, std::ios::beg);
        
        data.resize(size);
        file.read(reinterpret_cast<char*>(data.data()), size);
        file.close();
        
    } catch (const std::exception& e) {
        logError("Failed to read binary file: " + std::string(e.what()));
    }
    
    return data;
}

bool writeBinaryFile(const std::string& path, const std::vector<uint8_t>& data) {
    try {
        std::ofstream file(path, std::ios::binary);
        if (!file.is_open()) {
            return false;
        }
        
        file.write(reinterpret_cast<const char*>(data.data()), data.size());
        file.close();
        return true;
        
    } catch (const std::exception& e) {
        logError("Failed to write binary file: " + std::string(e.what()));
        return false;
    }
}

std::string trim(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) return "";
    
    size_t end = str.find_last_not_of(" \t\r\n");
    return str.substr(start, end - start + 1);
}

std::vector<std::string> split(const std::string& str, char delimiter) {
    std::vector<std::string> tokens;
    std::stringstream ss(str);
    std::string token;
    
    while (std::getline(ss, token, delimiter)) {
        tokens.push_back(trim(token));
    }
    
    return tokens;
}

std::string toLower(const std::string& str) {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

bool isValidImageFormat(const std::vector<uint8_t>& data) {
    if (data.size() < 4) return false;
    
    // Check for common image signatures
    // JPEG
    if (data[0] == 0xFF && data[1] == 0xD8) return true;
    
    // PNG
    if (data[0] == 0x89 && data[1] == 0x50 && data[2] == 0x4E && data[3] == 0x47) return true;
    
    // BMP
    if (data[0] == 0x42 && data[1] == 0x4D) return true;
    
    return false;
}

bool isValidVideoFormat(const std::vector<uint8_t>& data) {
    if (data.size() < 8) return false;
    
    // Check for common video signatures
    // MP4
    if (data.size() > 8) {
        std::string ftyp(data.begin() + 4, data.begin() + 8);
        if (ftyp == "ftyp") return true;
    }
    
    // AVI
    if (data[0] == 0x52 && data[1] == 0x49 && data[2] == 0x46 && data[3] == 0x46) {
        if (data[8] == 0x41 && data[9] == 0x56 && data[10] == 0x49) return true;
    }
    
    // WebM
    if (data[0] == 0x1A && data[1] == 0x45 && data[2] == 0xDF && data[3] == 0xA3) return true;
    
    return false;
}

cv::Mat bufferToMat(const std::vector<uint8_t>& buffer) {
    try {
        return cv::imdecode(buffer, cv::IMREAD_COLOR);
    } catch (const std::exception& e) {
        logError("Failed to decode buffer to Mat: " + std::string(e.what()));
        return cv::Mat();
    }
}

void logInfo(const std::string& message) {
    std::cout << "[INFO] " << getCurrentTimeString() << " - " << message << std::endl;
}

void logWarning(const std::string& message) {
    std::cout << "[WARN] " << getCurrentTimeString() << " - " << message << std::endl;
}

void logError(const std::string& message) {
    std::cerr << "[ERROR] " << getCurrentTimeString() << " - " << message << std::endl;
}

std::string getCurrentTimeString() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    return ss.str();
}

int64_t getCurrentTimestamp() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
}

}
