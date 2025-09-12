#pragma once

#include "common.h"
#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>
#include <vector>

class FaceDetector {
public:
    FaceDetector();
    ~FaceDetector();
    
    bool initialize(const std::string& model_path = "");
    std::vector<cv::Rect> detectFaces(const cv::Mat& image, float confidence_threshold = FACE_CONFIDENCE_THRESHOLD);
    cv::Mat preprocessFace(const cv::Mat& image, const cv::Rect& face_rect);
    
private:
    cv::dnn::Net net_;
    bool initialized_;
    
    // Canny edge detection for background removal
    cv::Mat removeBackgroundCanny(const cv::Mat& image);
    
    // Skin tone normalization
    cv::Mat normalizeSkinTone(const cv::Mat& image);
    
    // Face alignment and cropping
    cv::Mat alignAndCropFace(const cv::Mat& image, const cv::Rect& face_rect);
};
