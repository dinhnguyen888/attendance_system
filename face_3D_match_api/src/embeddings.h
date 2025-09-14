#pragma once
#include <opencv2/opencv.hpp>
#include <vector>
#include <string>
#include "arcface_processor.h"

typedef std::vector<float> Embedding;

struct ComparisonResult {
    bool match = false;
    float similarity = 0.0f;
    std::string message;
    cv::Mat comparison_image;
    
    ComparisonResult() : match(false), similarity(0.0f) {}
    ComparisonResult(bool m, float sim, const std::string& msg, const cv::Mat& img = cv::Mat())
        : match(m), similarity(sim), message(msg), comparison_image(img) {}
};

// Legacy functions for backward compatibility
bool initialize_dnn_model(const std::string& modelPath);
std::vector<Embedding> compute_embeddings(const std::vector<cv::Mat>& preprocessed);
Embedding compute_mean_embedding(const std::vector<Embedding>& embs);
std::vector<Embedding> load_employee_embeddings(const std::string& employeeId);
Embedding load_mean_embedding(const std::string& employeeId);
ComparisonResult compare_face_embedding(const Embedding& input_embedding, const std::string& employeeId);

// New ArcFace-based functions
ArcFaceProcessor& get_arcface_processor();
bool initialize_arcface_pipeline(const std::string& arcface_model_path = "models/resnet100.onnx",
                                const std::string& detector_model_path = "models/retinaface.onnx");
ArcFaceResult process_face_with_arcface(const cv::Mat& image);
FaceMatchResult match_face_with_arcface(const std::vector<float>& embedding, const std::string& employee_id);


