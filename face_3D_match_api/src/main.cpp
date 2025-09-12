#include "api_server.h"
#include "utils.h"
#include <iostream>
#include <string>
#include <signal.h>

// Global server instance for signal handling
ApiServer* g_server = nullptr;

void signalHandler(int signal) {
    if (g_server) {
        Utils::logInfo("Received signal " + std::to_string(signal) + ", shutting down server...");
        g_server->stop();
    }
    exit(0);
}

int main(int argc, char* argv[]) {
    try {
        Utils::logInfo("Starting Face 3D Match API Server...");
        
        // Default configuration
        std::string model_path = "models/resnet100.onnx";
        int port = 8080;
        
        // Parse command line arguments
        for (int i = 1; i < argc; i++) {
            std::string arg = argv[i];
            
            if (arg == "--model" && i + 1 < argc) {
                model_path = argv[++i];
            } else if (arg == "--port" && i + 1 < argc) {
                port = std::stoi(argv[++i]);
            } else if (arg == "--help" || arg == "-h") {
                std::cout << "Face 3D Match API Server\n"
                          << "Usage: " << argv[0] << " [options]\n"
                          << "Options:\n"
                          << "  --model <path>    Path to ArcFace ONNX model (default: models/resnet100.onnx)\n"
                          << "  --port <number>   Server port (default: 8080)\n"
                          << "  --help, -h        Show this help message\n"
                          << "\nEndpoints:\n"
                          << "  POST /api/register     - Register employee with video\n"
                          << "  POST /api/check-in     - Employee check-in with video\n"
                          << "  POST /api/check-out    - Employee check-out with video\n"
                          << "  POST /api/upload-3x4   - Upload 3x4 photo (placeholder)\n"
                          << "  GET  /api/health       - Health check\n"
                          << std::endl;
                return 0;
            }
        }
        
        // Check if model file exists
        if (!Utils::fileExists(model_path)) {
            Utils::logError("ArcFace model file not found: " + model_path);
            Utils::logInfo("Please ensure the ArcFace model is available at the specified path");
            Utils::logInfo("You can download it from: https://github.com/onnx/models/tree/main/vision/body_analysis/arcface");
            return 1;
        }
        
        // Create and initialize server
        ApiServer server;
        g_server = &server;
        
        // Setup signal handlers for graceful shutdown
        signal(SIGINT, signalHandler);
        signal(SIGTERM, signalHandler);
        
        if (!server.initialize(model_path, port)) {
            Utils::logError("Failed to initialize API server");
            return 1;
        }
        
        Utils::logInfo("=== Face 3D Match API Server ===");
        Utils::logInfo("Model: " + model_path);
        Utils::logInfo("Port: " + std::to_string(port));
        Utils::logInfo("Endpoints:");
        Utils::logInfo("  POST http://localhost:" + std::to_string(port) + "/api/register");
        Utils::logInfo("  POST http://localhost:" + std::to_string(port) + "/api/check-in");
        Utils::logInfo("  POST http://localhost:" + std::to_string(port) + "/api/check-out");
        Utils::logInfo("  POST http://localhost:" + std::to_string(port) + "/api/upload-3x4");
        Utils::logInfo("  GET  http://localhost:" + std::to_string(port) + "/api/health");
        Utils::logInfo("================================");
        
        // Start server (blocking call)
        server.start();
        
    } catch (const std::exception& e) {
        Utils::logError("Server error: " + std::string(e.what()));
        return 1;
    } catch (...) {
        Utils::logError("Unknown server error occurred");
        return 1;
    }
    
    return 0;
}