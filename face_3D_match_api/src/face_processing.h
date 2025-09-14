#pragma once
#include <opencv2/opencv.hpp>
#include <vector>
#include "embeddings.h"

// face detection and processing functions
cv::Rect detect_largest_face(const cv::Mat& frame);
cv::Mat crop_and_enhance_face(const cv::Mat& frame, const cv::Rect& face_rect);
cv::Mat enhance_image_quality(const cv::Mat& img);
cv::Mat apply_super_resolution(const cv::Mat& img);
cv::Mat denoise_image(const cv::Mat& img);
cv::Mat sharpen_image(const cv::Mat& img);

// preprocessing function with face detection and quality improvement
std::vector<cv::Mat> preprocess_faces(const std::vector<cv::Mat>& frames);
