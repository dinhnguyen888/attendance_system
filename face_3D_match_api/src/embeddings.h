#pragma once
#include <opencv2/opencv.hpp>
#include <vector>

using Embedding = std::vector<float>;

// Initialize OpenCV DNN model
bool initialize_dnn_model(const std::string& modelPath);

// Compute embeddings using OpenCV DNN
std::vector<Embedding> compute_embeddings(const std::vector<cv::Mat>& preprocessed);
Embedding compute_mean_embedding(const std::vector<Embedding>& embs);

// Load embeddings from file system
std::vector<Embedding> load_employee_embeddings(const std::string& employeeId);
Embedding load_mean_embedding(const std::string& employeeId);

// Compare embeddings for face recognition
struct ComparisonResult {
    bool match;
    float similarity;
    std::string message;
    cv::Mat comparison_image;
    
    ComparisonResult() : match(false), similarity(0.0f) {}
    ComparisonResult(bool m, float sim, const std::string& msg, const cv::Mat& img)
        : match(m), similarity(sim), message(msg), comparison_image(img) {}
};

ComparisonResult compare_face_embedding(const Embedding& input_embedding, const std::string& employeeId);


