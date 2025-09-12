#include "face_detector.h"
#include <opencv2/imgproc.hpp>
#include <iostream>

FaceDetector::FaceDetector() : initialized_(false) {}

FaceDetector::~FaceDetector() {}

bool FaceDetector::initialize(const std::string& model_path) {
    try {
        // Use OpenCV's built-in face detector if no model path provided
        if (model_path.empty()) {
            // Using Haar cascade as fallback
            initialized_ = true;
            return true;
        }
        
        // Load DNN model if provided
        net_ = cv::dnn::readNetFromONNX(model_path);
        if (net_.empty()) {
            std::cerr << "Failed to load face detection model: " << model_path << std::endl;
            return false;
        }
        
        initialized_ = true;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Face detector initialization error: " << e.what() << std::endl;
        return false;
    }
}

std::vector<cv::Rect> FaceDetector::detectFaces(const cv::Mat& image, float confidence_threshold) {
    std::vector<cv::Rect> faces;
    
    if (!initialized_ || image.empty()) {
        return faces;
    }
    
    try {
        // Use OpenCV's built-in cascade classifier as primary method
        cv::CascadeClassifier face_cascade;
        // Look for cascade file in /app/cascade directory first, then fall back to OpenCV samples
        std::string cascade_path = "/app/cascade/haarcascade_frontalface_alt.xml";
        if (!face_cascade.load(cascade_path)) {
            // Fall back to OpenCV samples if not found in /app/cascade
            cascade_path = cv::samples::findFile("haarcascade_frontalface_alt.xml");
        }
        if (face_cascade.load(cascade_path)) {
            std::vector<cv::Rect> detected_faces;
            cv::Mat gray;
            cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);
            cv::equalizeHist(gray, gray);
            
            face_cascade.detectMultiScale(gray, detected_faces, 1.1, 3, 0, cv::Size(MIN_FACE_SIZE, MIN_FACE_SIZE));
            
            // Filter faces by size and aspect ratio
            for (const auto& face : detected_faces) {
                if (face.width >= MIN_FACE_SIZE && face.height >= MIN_FACE_SIZE) {
                    float aspect_ratio = static_cast<float>(face.width) / face.height;
                    if (aspect_ratio > 0.7f && aspect_ratio < 1.4f) {
                        faces.push_back(face);
                    }
                }
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "Face detection error: " << e.what() << std::endl;
    }
    
    return faces;
}

cv::Mat FaceDetector::preprocessFace(const cv::Mat& image, const cv::Rect& face_rect) {
    if (image.empty() || face_rect.area() == 0) {
        return cv::Mat();
    }
    
    try {
        // Extract face region with padding
        cv::Rect expanded_rect = face_rect;
        int padding = static_cast<int>(face_rect.width * 0.2);
        expanded_rect.x = std::max(0, face_rect.x - padding);
        expanded_rect.y = std::max(0, face_rect.y - padding);
        expanded_rect.width = std::min(image.cols - expanded_rect.x, face_rect.width + 2 * padding);
        expanded_rect.height = std::min(image.rows - expanded_rect.y, face_rect.height + 2 * padding);
        
        cv::Mat face_roi = image(expanded_rect).clone();
        
        // Apply preprocessing pipeline
        cv::Mat processed = removeBackgroundCanny(face_roi);
        processed = normalizeSkinTone(processed);
        processed = alignAndCropFace(processed, cv::Rect(padding, padding, face_rect.width, face_rect.height));
        
        return processed;
    } catch (const std::exception& e) {
        std::cerr << "Face preprocessing error: " << e.what() << std::endl;
        return image(face_rect).clone();
    }
}

cv::Mat FaceDetector::removeBackgroundCanny(const cv::Mat& image) {
    if (image.empty()) return image;
    
    try {
        cv::Mat gray, edges, mask;
        cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);
        
        // Apply Gaussian blur to reduce noise
        cv::GaussianBlur(gray, gray, cv::Size(5, 5), 1.5);
        
        // Canny edge detection
        cv::Canny(gray, edges, 50, 150);
        
        // Dilate edges to create mask
        cv::Mat kernel = cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(5, 5));
        cv::dilate(edges, mask, kernel, cv::Point(-1, -1), 2);
        
        // Invert mask (we want to keep the face, not the edges)
        cv::bitwise_not(mask, mask);
        
        // Apply mask to original image
        cv::Mat result;
        image.copyTo(result, mask);
        
        // Fill background with neutral color
        cv::Mat background = cv::Mat::ones(image.size(), image.type()) * cv::Scalar(128, 128, 128);
        cv::Mat inv_mask;
        cv::bitwise_not(mask, inv_mask);
        background.copyTo(result, inv_mask);
        
        return result;
    } catch (const std::exception& e) {
        std::cerr << "Background removal error: " << e.what() << std::endl;
        return image;
    }
}

cv::Mat FaceDetector::normalizeSkinTone(const cv::Mat& image) {
    if (image.empty()) return image;
    
    try {
        cv::Mat result;
        image.copyTo(result);
        
        // Convert to YUV color space for better skin tone processing
        cv::Mat yuv;
        cv::cvtColor(result, yuv, cv::COLOR_BGR2YUV);
        
        // Apply histogram equalization to Y channel
        std::vector<cv::Mat> channels;
        cv::split(yuv, channels);
        cv::equalizeHist(channels[0], channels[0]);
        cv::merge(channels, yuv);
        
        // Convert back to BGR
        cv::cvtColor(yuv, result, cv::COLOR_YUV2BGR);
        
        // Apply slight Gaussian blur for smoothing
        cv::GaussianBlur(result, result, cv::Size(3, 3), 0.5);
        
        return result;
    } catch (const std::exception& e) {
        std::cerr << "Skin tone normalization error: " << e.what() << std::endl;
        return image;
    }
}

cv::Mat FaceDetector::alignAndCropFace(const cv::Mat& image, const cv::Rect& face_rect) {
    if (image.empty() || face_rect.area() == 0) return image;
    
    try {
        // Ensure face rect is within image bounds
        cv::Rect safe_rect = face_rect & cv::Rect(0, 0, image.cols, image.rows);
        if (safe_rect.area() == 0) return image;
        
        cv::Mat face = image(safe_rect).clone();
        
        // Resize to standard size for embedding (112x112 for ArcFace)
        cv::Mat resized;
        cv::resize(face, resized, cv::Size(112, 112), 0, 0, cv::INTER_LINEAR);
        
        // Normalize pixel values
        resized.convertTo(resized, CV_32F, 1.0/255.0);
        
        return resized;
    } catch (const std::exception& e) {
        std::cerr << "Face alignment error: " << e.what() << std::endl;
        return image;
    }
}
