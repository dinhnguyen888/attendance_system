#pragma once
#include <opencv2/opencv.hpp>
#include <vector>

class FaceAlignment {
public:
    FaceAlignment();
    
    // Align face using 5-point landmarks to standard template
    cv::Mat align_face(const cv::Mat& image, const std::vector<cv::Point2f>& landmarks, 
                       cv::Size output_size = cv::Size(112, 112));
    
    // Get standard 5-point template for ArcFace (112x112)
    static std::vector<cv::Point2f> get_arcface_template();
    
    // Alternative alignment methods
    cv::Mat align_face_similarity(const cv::Mat& image, const std::vector<cv::Point2f>& landmarks,
                                  cv::Size output_size = cv::Size(112, 112));
    
private:
    // Standard ArcFace 5-point template (normalized to 112x112)
    std::vector<cv::Point2f> arcface_template_;
    
    // Helper functions
    cv::Mat estimate_similarity_transform(const std::vector<cv::Point2f>& src_points,
                                         const std::vector<cv::Point2f>& dst_points);
    cv::Mat estimate_affine_transform(const std::vector<cv::Point2f>& src_points,
                                     const std::vector<cv::Point2f>& dst_points);
};
