#pragma once
#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>
#include <vector>

struct FaceDetection {
    cv::Rect bbox;
    float confidence;
    std::vector<cv::Point2f> landmarks; // 5 points: left_eye, right_eye, nose, left_mouth, right_mouth
};

class FaceDetector {
public:
    FaceDetector();
    ~FaceDetector();
    
    bool initialize(const std::string& model_path = "models/retinaface.onnx");
    std::vector<FaceDetection> detect_faces(const cv::Mat& image, float conf_threshold = 0.8f);
    
private:
    cv::dnn::Net net_;
    bool initialized_;
    
    // Helper functions
    std::vector<FaceDetection> post_process(const cv::Mat& output, const cv::Size& input_size, 
                                          const cv::Size& original_size, float conf_threshold);
    cv::Mat preprocess_image(const cv::Mat& image, cv::Size target_size = cv::Size(640, 640));
};

// Fallback MTCNN-style detector using OpenCV
class MTCNNFaceDetector {
public:
    MTCNNFaceDetector();
    bool initialize();
    std::vector<FaceDetection> detect_faces(const cv::Mat& image, float conf_threshold = 0.7f);
    
private:
    cv::CascadeClassifier face_cascade_;
    cv::dnn::Net landmark_net_;
    bool initialized_;
    
    std::vector<cv::Point2f> detect_landmarks(const cv::Mat& face_roi);
};
