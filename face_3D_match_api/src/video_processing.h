#pragma once
#include <opencv2/opencv.hpp>
#include <vector>
#include <string>

struct ValidationResult {
    bool ok;
    std::string message;
};

ValidationResult validate_video_faces(const std::vector<uint8_t>& videoBytes);
std::vector<cv::Mat> extract_representative_frames(const std::vector<uint8_t>& videoBytes, int numSegments);
std::vector<cv::Mat> extract_representative_frames_from_file(const std::string& videoPath, int numSegments);


