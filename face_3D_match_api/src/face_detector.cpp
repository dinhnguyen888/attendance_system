#include "face_detector.h"
#include <iostream>
#include <algorithm>

// RetinaFace-based detector
FaceDetector::FaceDetector() : initialized_(false) {}

FaceDetector::~FaceDetector() {}

bool FaceDetector::initialize(const std::string& model_path) {
    try {
        // Try to load RetinaFace or similar face detection model
        net_ = cv::dnn::readNetFromONNX(model_path);
        if (net_.empty()) {
            std::cout << "[WARNING] Failed to load face detection model: " << model_path << std::endl;
            return false;
        }
        
        // Set backend and target
        net_.setPreferableBackend(cv::dnn::DNN_BACKEND_OPENCV);
        net_.setPreferableTarget(cv::dnn::DNN_TARGET_CPU);
        
        initialized_ = true;
        std::cout << "[INFO] Face detector initialized successfully" << std::endl;
        return true;
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception initializing face detector: " << e.what() << std::endl;
        return false;
    }
}

cv::Mat FaceDetector::preprocess_image(const cv::Mat& image, cv::Size target_size) {
    cv::Mat blob;
    cv::dnn::blobFromImage(image, blob, 1.0, target_size, cv::Scalar(104, 117, 123), false, false, CV_32F);
    return blob;
}

std::vector<FaceDetection> FaceDetector::detect_faces(const cv::Mat& image, float conf_threshold) {
    std::vector<FaceDetection> detections;
    
    if (!initialized_ || image.empty()) {
        return detections;
    }
    
    try {
        // Preprocess
        cv::Mat blob = preprocess_image(image, cv::Size(640, 640));
        
        // Forward pass
        net_.setInput(blob);
        cv::Mat output = net_.forward();
        
        // Post-process
        detections = post_process(output, cv::Size(640, 640), image.size(), conf_threshold);
        
        std::cout << "[DEBUG] Detected " << detections.size() << " faces" << std::endl;
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Face detection failed: " << e.what() << std::endl;
    }
    
    return detections;
}

std::vector<FaceDetection> FaceDetector::post_process(const cv::Mat& output, const cv::Size& input_size, 
                                                     const cv::Size& original_size, float conf_threshold) {
    std::vector<FaceDetection> detections;
    
    // This is a simplified post-processing for RetinaFace
    // In practice, you'd need to implement anchor generation and NMS
    // For now, we'll use a basic approach
    
    float scale_x = static_cast<float>(original_size.width) / input_size.width;
    float scale_y = static_cast<float>(original_size.height) / input_size.height;
    
    // Parse output (this depends on the specific model format)
    // Assuming output format: [batch, num_detections, 15] where 15 = [x1,y1,x2,y2,conf,lx1,ly1,rx1,ry1,nx,ny,lmx,lmy,rmx,rmy]
    
    if (output.dims >= 2 && output.size[1] > 0) {
        const float* data = (float*)output.data;
        int num_detections = output.size[1];
        
        for (int i = 0; i < num_detections; ++i) {
            float confidence = data[i * 15 + 4];
            
            if (confidence > conf_threshold) {
                FaceDetection detection;
                detection.confidence = confidence;
                
                // Bounding box
                float x1 = data[i * 15 + 0] * scale_x;
                float y1 = data[i * 15 + 1] * scale_y;
                float x2 = data[i * 15 + 2] * scale_x;
                float y2 = data[i * 15 + 3] * scale_y;
                
                detection.bbox = cv::Rect(cv::Point(x1, y1), cv::Point(x2, y2));
                
                // 5-point landmarks
                detection.landmarks.resize(5);
                for (int j = 0; j < 5; ++j) {
                    detection.landmarks[j].x = data[i * 15 + 5 + j * 2] * scale_x;
                    detection.landmarks[j].y = data[i * 15 + 6 + j * 2] * scale_y;
                }
                
                detections.push_back(detection);
            }
        }
    }
    
    return detections;
}

// MTCNN-style fallback detector
MTCNNFaceDetector::MTCNNFaceDetector() : initialized_(false) {}

bool MTCNNFaceDetector::initialize() {
    try {
        // Load Haar cascade for face detection
        if (!face_cascade_.load("/app/cascade/haarcascade_frontalface_alt.xml")) {
            std::cout << "[ERROR] Cannot load face cascade" << std::endl;
            return false;
        }
        
        // Try to load a simple landmark detection model (if available)
        try {
            landmark_net_ = cv::dnn::readNetFromONNX("models/landmarks.onnx");
        } catch (...) {
            std::cout << "[WARNING] Landmark model not available, will use geometric estimation" << std::endl;
        }
        
        initialized_ = true;
        std::cout << "[INFO] MTCNN-style face detector initialized" << std::endl;
        return true;
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception initializing MTCNN detector: " << e.what() << std::endl;
        return false;
    }
}

std::vector<FaceDetection> MTCNNFaceDetector::detect_faces(const cv::Mat& image, float conf_threshold) {
    std::vector<FaceDetection> detections;
    
    if (!initialized_ || image.empty()) {
        return detections;
    }
    
    cv::Mat gray;
    cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);
    
    std::vector<cv::Rect> faces;
    face_cascade_.detectMultiScale(gray, faces, 1.1, 3, 0, cv::Size(60, 60));
    
    for (const auto& face : faces) {
        FaceDetection detection;
        detection.bbox = face;
        detection.confidence = 0.9f; // Haar cascade doesn't provide confidence
        
        // Extract face ROI for landmark detection
        cv::Mat face_roi = image(face);
        detection.landmarks = detect_landmarks(face_roi);
        
        // Convert relative landmarks to absolute coordinates
        for (auto& landmark : detection.landmarks) {
            landmark.x += face.x;
            landmark.y += face.y;
        }
        
        detections.push_back(detection);
    }
    
    std::cout << "[DEBUG] MTCNN-style detector found " << detections.size() << " faces" << std::endl;
    return detections;
}

std::vector<cv::Point2f> MTCNNFaceDetector::detect_landmarks(const cv::Mat& face_roi) {
    std::vector<cv::Point2f> landmarks(5);
    
    if (!landmark_net_.empty()) {
        try {
            // Use DNN model for landmark detection
            cv::Mat blob = cv::dnn::blobFromImage(face_roi, 1.0/255.0, cv::Size(96, 96), cv::Scalar(0, 0, 0), true, false);
            landmark_net_.setInput(blob);
            cv::Mat output = landmark_net_.forward();
            
            if (output.total() >= 10) { // 5 points * 2 coordinates
                const float* data = (float*)output.data;
                for (int i = 0; i < 5; ++i) {
                    landmarks[i].x = data[i * 2] * face_roi.cols;
                    landmarks[i].y = data[i * 2 + 1] * face_roi.rows;
                }
            }
        } catch (...) {
            // Fall back to geometric estimation
        }
    }
    
    // Geometric estimation as fallback
    if (landmarks[0].x == 0 && landmarks[0].y == 0) {
        float w = face_roi.cols;
        float h = face_roi.rows;
        
        // Approximate 5-point landmarks based on face geometry
        landmarks[0] = cv::Point2f(w * 0.3f, h * 0.4f);  // Left eye
        landmarks[1] = cv::Point2f(w * 0.7f, h * 0.4f);  // Right eye
        landmarks[2] = cv::Point2f(w * 0.5f, h * 0.6f);  // Nose tip
        landmarks[3] = cv::Point2f(w * 0.35f, h * 0.8f); // Left mouth corner
        landmarks[4] = cv::Point2f(w * 0.65f, h * 0.8f); // Right mouth corner
    }
    
    return landmarks;
}
