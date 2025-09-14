#include "face_alignment.h"
#include <iostream>

FaceAlignment::FaceAlignment() {
    // Initialize ArcFace standard template for 112x112 images
    arcface_template_ = get_arcface_template();
}

std::vector<cv::Point2f> FaceAlignment::get_arcface_template() {
    // Standard 5-point template for ArcFace models (112x112 resolution)
    // Order: left_eye, right_eye, nose_tip, left_mouth_corner, right_mouth_corner
    std::vector<cv::Point2f> template_points = {
        cv::Point2f(30.2946f, 51.6963f),   // Left eye
        cv::Point2f(65.5318f, 51.5014f),   // Right eye  
        cv::Point2f(48.0252f, 71.7366f),   // Nose tip
        cv::Point2f(33.5493f, 92.3655f),   // Left mouth corner
        cv::Point2f(62.7299f, 92.2041f)    // Right mouth corner
    };
    return template_points;
}

cv::Mat FaceAlignment::align_face(const cv::Mat& image, const std::vector<cv::Point2f>& landmarks, 
                                  cv::Size output_size) {
    if (landmarks.size() != 5) {
        std::cout << "[ERROR] Face alignment requires exactly 5 landmarks, got " << landmarks.size() << std::endl;
        return cv::Mat();
    }
    
    if (image.empty()) {
        std::cout << "[ERROR] Input image is empty" << std::endl;
        return cv::Mat();
    }
    
    try {
        // Scale template to output size if different from 112x112
        std::vector<cv::Point2f> scaled_template = arcface_template_;
        if (output_size.width != 112 || output_size.height != 112) {
            float scale_x = static_cast<float>(output_size.width) / 112.0f;
            float scale_y = static_cast<float>(output_size.height) / 112.0f;
            
            for (auto& point : scaled_template) {
                point.x *= scale_x;
                point.y *= scale_y;
            }
        }
        
        // Estimate similarity transformation (scale, rotation, translation)
        cv::Mat transform = estimate_similarity_transform(landmarks, scaled_template);
        
        if (transform.empty()) {
            std::cout << "[ERROR] Failed to estimate transformation matrix" << std::endl;
            return cv::Mat();
        }
        
        // Apply transformation
        cv::Mat aligned_face;
        cv::warpAffine(image, aligned_face, transform, output_size, cv::INTER_LINEAR, cv::BORDER_CONSTANT, cv::Scalar(0, 0, 0));
        
        std::cout << "[DEBUG] Face aligned successfully to size " << output_size << std::endl;
        return aligned_face;
        
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception during face alignment: " << e.what() << std::endl;
        return cv::Mat();
    }
}

cv::Mat FaceAlignment::align_face_similarity(const cv::Mat& image, const std::vector<cv::Point2f>& landmarks,
                                            cv::Size output_size) {
    if (landmarks.size() < 2) {
        std::cout << "[ERROR] Need at least 2 landmarks for similarity alignment" << std::endl;
        return cv::Mat();
    }
    
    // Use only eye points for similarity transformation
    cv::Point2f left_eye = landmarks[0];
    cv::Point2f right_eye = landmarks[1];
    
    // Calculate eye center and angle
    cv::Point2f eye_center = (left_eye + right_eye) * 0.5f;
    cv::Point2f eye_direction = right_eye - left_eye;
    float angle = atan2(eye_direction.y, eye_direction.x) * 180.0f / CV_PI;
    
    // Calculate scale based on eye distance
    float eye_distance = cv::norm(eye_direction);
    float desired_eye_distance = 35.0f; // Standard distance for 112x112
    float scale = desired_eye_distance / eye_distance;
    
    if (output_size.width != 112 || output_size.height != 112) {
        scale *= static_cast<float>(output_size.width) / 112.0f;
    }
    
    // Create transformation matrix
    cv::Point2f center(output_size.width * 0.5f, output_size.height * 0.5f);
    cv::Mat transform = cv::getRotationMatrix2D(eye_center, angle, scale);
    
    // Adjust translation to center the face
    transform.at<double>(0, 2) += center.x - eye_center.x;
    transform.at<double>(1, 2) += center.y - eye_center.y;
    
    // Apply transformation
    cv::Mat aligned_face;
    cv::warpAffine(image, aligned_face, transform, output_size, cv::INTER_LINEAR);
    
    return aligned_face;
}

cv::Mat FaceAlignment::estimate_similarity_transform(const std::vector<cv::Point2f>& src_points,
                                                    const std::vector<cv::Point2f>& dst_points) {
    if (src_points.size() != dst_points.size() || src_points.size() < 2) {
        return cv::Mat();
    }
    
    try {
        // Use OpenCV's estimateAffinePartial2D for similarity transform
        cv::Mat transform = cv::estimateAffinePartial2D(src_points, dst_points, cv::noArray(), 
                                                       cv::RANSAC, 3.0, 2000, 0.99, 10);
        
        if (transform.empty()) {
            // Fallback to simple affine transform
            transform = cv::getAffineTransform(
                std::vector<cv::Point2f>(src_points.begin(), src_points.begin() + 3),
                std::vector<cv::Point2f>(dst_points.begin(), dst_points.begin() + 3)
            );
        }
        
        return transform;
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception in similarity transform estimation: " << e.what() << std::endl;
        return cv::Mat();
    }
}

cv::Mat FaceAlignment::estimate_affine_transform(const std::vector<cv::Point2f>& src_points,
                                                const std::vector<cv::Point2f>& dst_points) {
    if (src_points.size() < 3 || dst_points.size() < 3) {
        return cv::Mat();
    }
    
    try {
        // Use first 3 points for affine transformation
        std::vector<cv::Point2f> src_3(src_points.begin(), src_points.begin() + 3);
        std::vector<cv::Point2f> dst_3(dst_points.begin(), dst_points.begin() + 3);
        
        return cv::getAffineTransform(src_3, dst_3);
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception in affine transform estimation: " << e.what() << std::endl;
        return cv::Mat();
    }
}
