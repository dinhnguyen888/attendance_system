#pragma once
#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>
#include <vector>
#include "face_detector.h"
#include "face_alignment.h"

struct ArcFaceResult {
    bool success;
    std::vector<float> embedding;
    float confidence;
    std::string message;
    cv::Mat aligned_face; // For debugging/visualization
};

struct FaceMatchResult {
    bool match;
    float similarity;
    float confidence;
    std::string message;
    std::string best_match_id;
};

class ArcFaceProcessor {
public:
    ArcFaceProcessor();
    ~ArcFaceProcessor();
    
    // Initialize the complete pipeline
    bool initialize(const std::string& arcface_model_path = "models/resnet100.onnx",
                   const std::string& detector_model_path = "models/retinaface.onnx");
    
    // Complete pipeline: detect -> align -> extract embedding
    ArcFaceResult process_face(const cv::Mat& image, bool return_largest_face = true);
    
    // Extract embedding from aligned face
    std::vector<float> extract_embedding(const cv::Mat& aligned_face);
    
    // Compare embeddings using proper ArcFace similarity
    float calculate_similarity(const std::vector<float>& embedding1, 
                              const std::vector<float>& embedding2);
    
    // Match face against stored embeddings
    FaceMatchResult match_face(const std::vector<float>& input_embedding, 
                              const std::string& employee_id,
                              float threshold = 0.4f);
    
    // Batch processing for multiple faces
    std::vector<ArcFaceResult> process_multiple_faces(const cv::Mat& image);
    
    // Utility functions
    std::vector<float> normalize_embedding(const std::vector<float>& embedding);
    bool save_embedding(const std::vector<float>& embedding, const std::string& file_path);
    std::vector<float> load_embedding(const std::string& file_path);
    
private:
    // Core components
    std::unique_ptr<FaceDetector> face_detector_;
    std::unique_ptr<MTCNNFaceDetector> fallback_detector_;
    std::unique_ptr<FaceAlignment> face_aligner_;
    
    cv::dnn::Net arcface_net_;
    bool initialized_;
    
    // Configuration
    cv::Size input_size_;  // 112x112 for ArcFace
    cv::Scalar mean_;      // Normalization mean
    cv::Scalar std_;       // Normalization std
    
    // Helper functions
    cv::Mat preprocess_for_arcface(const cv::Mat& aligned_face);
    std::vector<float> postprocess_embedding(const cv::Mat& net_output);
    std::vector<std::vector<float>> load_employee_embeddings(const std::string& employee_id);
};
