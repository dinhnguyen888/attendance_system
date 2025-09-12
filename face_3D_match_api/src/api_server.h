#pragma once

#include "common.h"
#include "face_recognizer.h"
#include <crow.h>
#include <memory>
#include <string>

class ApiServer {
public:
    ApiServer();
    ~ApiServer();
    
    bool initialize(const std::string& arcface_model_path, int port = 8080);
    void start();
    void stop();
    
private:
    crow::SimpleApp app_;
    std::unique_ptr<FaceRecognizer> face_recognizer_;
    bool initialized_;
    int port_;
    
    // Endpoint handlers
    crow::response handleRegister(const crow::request& req);
    crow::response handleCheckIn(const crow::request& req);
    crow::response handleCheckOut(const crow::request& req);
    crow::response handleUpload3x4(const crow::request& req);
    crow::response handleHealth(const crow::request& req);
    
    // Utility methods
    std::vector<uint8_t> extractVideoFromMultipart(const crow::request& req, std::string& employee_id);
    crow::response createErrorResponse(int code, const std::string& message);
    crow::response createSuccessResponse(const std::string& message);
    crow::response createSuccessResponse(const std::string& message, crow::json::wvalue&& data);
    
    // CORS headers
    void addCorsHeaders(crow::response& res);
    
    // Request validation
    bool validateRequest(const crow::request& req);
};
