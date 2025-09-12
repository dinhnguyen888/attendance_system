#pragma once

#include "common.h"
#include "face_detector.h"
#include "arcface_model.h"
#include <opencv2/opencv.hpp>
#include <vector>
#include <string>
#include <memory>
#include <unordered_map>

class FaceRecognizer {
public:
    FaceRecognizer();
    ~FaceRecognizer();
    
    bool initialize(const std::string& arcface_model_path);
    
    // Video processing methods
    std::vector<FaceEmbedding> processVideo(const std::string& video_path, int total_frames);
    std::vector<FaceEmbedding> processVideoFromBuffer(const std::vector<uint8_t>& video_buffer, int total_frames);
    
    // Employee management
    bool registerEmployee(const std::string& employee_id, const std::vector<FaceEmbedding>& embeddings);
    ComparisonResult verifyEmployee(const std::vector<FaceEmbedding>& query_embeddings);
    
    // Database operations
    bool saveEmployeeData(const std::string& employee_id, const std::vector<FaceEmbedding>& embeddings);
    bool loadEmployeeData();
    
private:
    std::unique_ptr<FaceDetector> face_detector_;
    std::unique_ptr<ArcFaceModel> arcface_model_;
    std::unordered_map<std::string, Employee> employee_database_;
    bool initialized_;
    
    // Video processing helpers
    std::vector<cv::Mat> extractFramesFromVideo(const std::string& video_path, int interval_seconds = VIDEO_FRAME_INTERVAL);
    std::vector<cv::Mat> extractFramesFromBuffer(const std::vector<uint8_t>& video_buffer, int interval_seconds = VIDEO_FRAME_INTERVAL);
    
    // Face processing pipeline
    std::vector<FaceEmbedding> processFacesInFrames(const std::vector<cv::Mat>& frames);
    
    // Comparison methods
    float compareEmbeddings(const std::vector<float>& embedding1, const std::vector<float>& embedding2);
    ComparisonResult findBestMatch(const std::vector<FaceEmbedding>& query_embeddings);
    
    // Utility methods
    std::string getCurrentTimestamp();
    bool createDirectoryIfNotExists(const std::string& path);
};
