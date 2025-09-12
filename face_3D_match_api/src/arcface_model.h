#pragma once

#include "common.h"
#include <opencv2/opencv.hpp>

#ifdef USE_ONNX_RUNTIME
#include <onnxruntime_cxx_api.h>
#endif

class ArcFaceModel {
public:
    ArcFaceModel();
    ~ArcFaceModel();
    
    bool initialize(const std::string& model_path);
    std::vector<float> extractEmbedding(const cv::Mat& face_image);
    float calculateSimilarity(const std::vector<float>& embedding1, const std::vector<float>& embedding2);
    
private:
    bool initialized_;
    
#ifdef USE_ONNX_RUNTIME
    std::unique_ptr<Ort::Env> env_;
    std::unique_ptr<Ort::Session> session_;
    std::unique_ptr<Ort::SessionOptions> session_options_;
    std::vector<const char*> input_names_;
    std::vector<const char*> output_names_;
    std::vector<std::string> input_name_storage_;
    std::vector<std::string> output_name_storage_;
    std::vector<int64_t> input_shape_;
#else
    cv::dnn::Net net_;
#endif
    
    // Preprocessing for ArcFace model
    cv::Mat preprocessForArcFace(const cv::Mat& face);
    
    // Normalize embedding vector
    std::vector<float> normalizeEmbedding(const std::vector<float>& embedding);
};
