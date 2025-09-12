#include "api_server.h"
#include <iostream>
#include <sstream>
#include <fstream>
#include <regex>

ApiServer::ApiServer() : initialized_(false), port_(8080) {
    face_recognizer_ = std::make_unique<FaceRecognizer>();
}

ApiServer::~ApiServer() {}

bool ApiServer::initialize(const std::string& arcface_model_path, int port) {
    try {
        port_ = port;
        
        if (!face_recognizer_->initialize(arcface_model_path)) {
            std::cerr << "Failed to initialize face recognizer" << std::endl;
            return false;
        }
        
        // Setup routes
        CROW_ROUTE(app_, "/api/register").methods("POST"_method)
        ([this](const crow::request& req) {
            return handleRegister(req);
        });
        
        CROW_ROUTE(app_, "/api/check-in").methods("POST"_method)
        ([this](const crow::request& req) {
            return handleCheckIn(req);
        });
        
        CROW_ROUTE(app_, "/api/check-out").methods("POST"_method)
        ([this](const crow::request& req) {
            return handleCheckOut(req);
        });
        
        CROW_ROUTE(app_, "/api/upload-3x4").methods("POST"_method)
        ([this](const crow::request& req) {
            return handleUpload3x4(req);
        });
        
        CROW_ROUTE(app_, "/api/health").methods("GET"_method)
        ([this](const crow::request& req) {
            return handleHealth(req);
        });
        
        // CORS preflight - Match all OPTIONS requests
        CROW_ROUTE(app_, "/api/<path>")
        .methods("OPTIONS"_method)
        ([this](const crow::request& req, const std::string& path) {
            crow::response res(200);
            addCorsHeaders(res);
            return res;
        });
        
        // Add CORS headers to all routes
        CROW_CATCHALL_ROUTE(app_)
        ([this](const crow::request& req) {
            if (req.method == crow::HTTPMethod::Options) {
                auto res = crow::response(200);
                addCorsHeaders(res);
                return res;
            }
            return crow::response(404);
        });
        
        initialized_ = true;
        std::cout << "API Server initialized on port " << port_ << std::endl;
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "API Server initialization error: " << e.what() << std::endl;
        return false;
    }
}

void ApiServer::start() {
    if (!initialized_) {
        std::cerr << "Server not initialized" << std::endl;
        return;
    }
    
    std::cout << "Starting Face 3D Match API server on port " << port_ << std::endl;
    app_.port(port_).multithreaded().run();
}

void ApiServer::stop() {
    app_.stop();
}

crow::response ApiServer::handleRegister(const crow::request& req) {
    try {
        std::string employee_id;
        std::vector<uint8_t> video_data = extractVideoFromMultipart(req, employee_id);
        
        if (video_data.empty() || employee_id.empty()) {
            return createErrorResponse(400, "Missing video data or employee ID");
        }
        
        // Process video to extract 10 frames (1 per second from 10s video)
        std::vector<FaceEmbedding> embeddings = face_recognizer_->processVideoFromBuffer(video_data, 10);
        
        if (embeddings.empty()) {
            return createErrorResponse(400, "No faces detected in video");
        }
        
        // Register employee with the extracted embeddings
        if (face_recognizer_->registerEmployee(employee_id, embeddings)) {
            crow::json::wvalue data;
            data["employee_id"] = employee_id;
            data["frames_processed"] = static_cast<int>(embeddings.size());
            data["message"] = "Employee registered successfully with " + std::to_string(embeddings.size()) + " frames";
            
            auto res = createSuccessResponse("Registration successful", std::move(data));
            addCorsHeaders(res);
            return res;
        } else {
            return createErrorResponse(500, "Failed to register employee with the provided video");
        }
        
    } catch (const std::exception& e) {
        auto res = createErrorResponse(500, std::string("Registration failed: ") + e.what());
        addCorsHeaders(res);
        return res;
    }
}

crow::response ApiServer::handleCheckIn(const crow::request& req) {
    try {
        std::string dummy_id;
        std::vector<uint8_t> video_data = extractVideoFromMultipart(req, dummy_id);
        
        if (video_data.empty()) {
            return createErrorResponse(400, "Missing video data");
        }
        
        // Process video to extract 3 frames (1 per second from 3s video)
        std::vector<FaceEmbedding> embeddings = face_recognizer_->processVideoFromBuffer(video_data, 3);
        
        if (embeddings.empty()) {
            return createErrorResponse(400, "No faces detected in video");
        }
        
        // Verify employee with the extracted embeddings
        ComparisonResult result = face_recognizer_->verifyEmployee(embeddings);
        
        if (result.match) {
            crow::json::wvalue data;
            data["employee_id"] = result.employee_id;
            data["similarity"] = result.similarity;
            data["frames_processed"] = static_cast<int>(embeddings.size());
            data["message"] = "Check-in successful with " + std::to_string(embeddings.size()) + " frames";
            
            crow::response res = createSuccessResponse("Check-in successful", std::move(data));
            addCorsHeaders(res);
            return res;
        } else {
            crow::response res = createErrorResponse(401, "Face not recognized: " + result.message);
            addCorsHeaders(res);
            return res;
        }
        
    } catch (const std::exception& e) {
        return createErrorResponse(500, "Check-in error: " + std::string(e.what()));
    }
}

crow::response ApiServer::handleCheckOut(const crow::request& req) {
    try {
        std::string dummy_id;
        std::vector<uint8_t> video_data = extractVideoFromMultipart(req, dummy_id);
        
        if (video_data.empty()) {
            return createErrorResponse(400, "Missing video data");
        }
        
        // Process video to extract 3 frames (1 per second from 3s video)
        std::vector<FaceEmbedding> embeddings = face_recognizer_->processVideoFromBuffer(video_data, 3);
        
        if (embeddings.empty()) {
            return createErrorResponse(400, "No faces detected in video");
        }
        
        // Verify employee with the extracted embeddings
        ComparisonResult result = face_recognizer_->verifyEmployee(embeddings);
        
        if (result.match) {
            crow::json::wvalue data;
            data["employee_id"] = result.employee_id;
            data["similarity"] = result.similarity;
            data["frames_processed"] = static_cast<int>(embeddings.size());
            data["message"] = "Check-out successful with " + std::to_string(embeddings.size()) + " frames";
            
            crow::response res = createSuccessResponse("Check-out successful", std::move(data));
            addCorsHeaders(res);
            return res;
        } else {
            crow::response res = createErrorResponse(401, "Face not recognized: " + result.message);
            addCorsHeaders(res);
            return res;
        }
        
    } catch (const std::exception& e) {
        return createErrorResponse(500, "Check-out error: " + std::string(e.what()));
    }
}

crow::response ApiServer::handleUpload3x4(const crow::request& req) {
    // Placeholder implementation
    crow::json::wvalue data;
    data["message"] = "3x4 photo upload endpoint - not implemented yet";
    data["status"] = "placeholder";
    
    crow::response res = createSuccessResponse("Upload 3x4 endpoint", std::move(data));
    addCorsHeaders(res);
    return res;
}

crow::response ApiServer::handleHealth(const crow::request& req) {
    crow::json::wvalue data;
    data["status"] = "healthy";
    data["service"] = "Face 3D Match API";
    data["version"] = "1.0.0";
    
    crow::response res = createSuccessResponse("Service is healthy", std::move(data));
    addCorsHeaders(res);
    return res;
}

std::vector<uint8_t> ApiServer::extractVideoFromMultipart(const crow::request& req, std::string& employee_id) {
    std::vector<uint8_t> video_data;
    
    try {
        std::string content_type = req.get_header_value("Content-Type");
        if (content_type.find("multipart/form-data") == std::string::npos) {
            return video_data;
        }
        
        // Extract boundary
        std::regex boundary_regex("boundary=([^;]+)");
        std::smatch boundary_match;
        std::string boundary;
        
        if (std::regex_search(content_type, boundary_match, boundary_regex)) {
            boundary = "--" + boundary_match[1].str();
        } else {
            return video_data;
        }
        
        std::string body = req.body;
        size_t pos = 0;
        
        while ((pos = body.find(boundary, pos)) != std::string::npos) {
            size_t header_start = pos + boundary.length();
            size_t header_end = body.find("\r\n\r\n", header_start);
            
            if (header_end == std::string::npos) break;
            
            std::string headers = body.substr(header_start, header_end - header_start);
            size_t data_start = header_end + 4;
            size_t data_end = body.find(boundary, data_start);
            
            if (data_end == std::string::npos) break;
            
            // Check if this is employee_id field
            if (headers.find("name=\"employee_id\"") != std::string::npos) {
                employee_id = body.substr(data_start, data_end - data_start - 2); // -2 for \r\n
            }
            // Check if this is video field
            else if (headers.find("name=\"video\"") != std::string::npos || 
                     headers.find("filename=") != std::string::npos) {
                std::string video_str = body.substr(data_start, data_end - data_start - 2);
                video_data.assign(video_str.begin(), video_str.end());
            }
            
            pos = data_end;
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Multipart extraction error: " << e.what() << std::endl;
    }
    
    return video_data;
}

crow::response ApiServer::createErrorResponse(int code, const std::string& message) {
    crow::json::wvalue response;
    response["success"] = false;
    response["error"] = message;
    response["code"] = code;

    crow::response res(code);
    res.set_header("Content-Type", "application/json");
    res.set_header("Access-Control-Allow-Origin", "*");
    res.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization");
    res.write(response.dump());
    return res;
}

crow::response ApiServer::createSuccessResponse(const std::string& message) {
    crow::json::wvalue response;
    response["success"] = true;
    response["message"] = message;

    crow::response res(200);
    res.set_header("Content-Type", "application/json");
    res.set_header("Access-Control-Allow-Origin", "*");
    res.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization");
    res.write(response.dump());
    return res;
}

crow::response ApiServer::createSuccessResponse(const std::string& message, crow::json::wvalue&& data) {
    crow::json::wvalue response;
    response["success"] = true;
    response["message"] = message;
    response["data"] = std::move(data);

    crow::response res(200);
    res.set_header("Content-Type", "application/json");
    res.set_header("Access-Control-Allow-Origin", "*");
    res.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization");
    res.write(response.dump());
    return res;
}

void ApiServer::addCorsHeaders(crow::response& res) {
    res.set_header("Access-Control-Allow-Origin", "*");
    res.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    res.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization");
}

bool ApiServer::validateRequest(const crow::request& req) {
    // Basic validation - can be extended
    return !req.body.empty();
}
