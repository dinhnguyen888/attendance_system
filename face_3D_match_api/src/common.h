#pragma once

#include <opencv2/opencv.hpp>
#include <vector>
#include <string>
#include <memory>

// Common data structures
struct FaceEmbedding {
    std::vector<float> features;
    cv::Rect bbox;
    float confidence;
    
    FaceEmbedding() : confidence(0.0f) {}
    FaceEmbedding(const std::vector<float>& feat, const cv::Rect& box, float conf)
        : features(feat), bbox(box), confidence(conf) {}
};

struct Employee {
    std::string id;
    std::vector<FaceEmbedding> embeddings;
    std::string created_at;
    
    Employee() = default;
    Employee(const std::string& emp_id) : id(emp_id) {}
};

struct ComparisonResult {
    bool match;
    float similarity;
    std::string employee_id;
    std::string message;
    
    ComparisonResult() : match(false), similarity(0.0f) {}
    ComparisonResult(bool m, float sim, const std::string& id, const std::string& msg)
        : match(m), similarity(sim), employee_id(id), message(msg) {}
};

// Constants
const float SIMILARITY_THRESHOLD = 0.75f;
const int MAX_EMBEDDINGS_PER_EMPLOYEE = 10;
const int VIDEO_FRAME_INTERVAL = 1; // Extract 1 frame per second
const int MIN_FACE_SIZE = 80;
const float FACE_CONFIDENCE_THRESHOLD = 0.8f;
