#include <crow.h>
#include <opencv2/opencv.hpp>
#include <iostream>
#include <string>
#include "server.h"
#include "embeddings.h"

int main(int argc, char* argv[]) {
    int port = 8080;
    std::string modelPath = "models/resnet100.onnx";
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = std::stoi(argv[++i]);
        } else if (arg == "--model" && i + 1 < argc) {
            modelPath = argv[++i];
        }
    }
    
    // Initialize ArcFace pipeline (new implementation)
    if (!initialize_arcface_pipeline(modelPath, "models/retinaface.onnx")) {
        std::cout << "[WARNING] ArcFace pipeline initialization failed, falling back to legacy DNN" << std::endl;
        // Fallback to legacy implementation
        if (!initialize_dnn_model(modelPath)) {
            std::cout << "[WARNING] Legacy DNN model initialization also failed, will use fallback" << std::endl;
        }
    }
    
    crow::SimpleApp app;
    register_routes(app);
    app.port(static_cast<uint16_t>(port)).multithreaded().run();
    return 0;
}