#pragma once

#include <string>
#include <vector>
#include <opencv2/opencv.hpp>

namespace Utils {
    // File operations
    bool fileExists(const std::string& path);
    std::vector<uint8_t> readBinaryFile(const std::string& path);
    bool writeBinaryFile(const std::string& path, const std::vector<uint8_t>& data);
    
    // String utilities
    std::string trim(const std::string& str);
    std::vector<std::string> split(const std::string& str, char delimiter);
    std::string toLower(const std::string& str);
    
    // Image utilities
    bool isValidImageFormat(const std::vector<uint8_t>& data);
    bool isValidVideoFormat(const std::vector<uint8_t>& data);
    cv::Mat bufferToMat(const std::vector<uint8_t>& buffer);
    
    // Logging
    void logInfo(const std::string& message);
    void logWarning(const std::string& message);
    void logError(const std::string& message);
    
    // Time utilities
    std::string getCurrentTimeString();
    int64_t getCurrentTimestamp();
}
