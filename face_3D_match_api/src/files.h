#pragma once
#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

std::string save_video(const std::string& employeeId, const std::vector<uint8_t>& bytes);
std::string save_frames(const std::string& employeeId, const std::vector<cv::Mat>& frames);
std::string save_preprocessed_frames(const std::string& employeeId, const std::vector<cv::Mat>& frames);
std::string save_embeddings(const std::string& employeeId, const std::vector<std::vector<float>>& embs);
bool save_mean_embedding(const std::string& employeeId, const std::vector<float>& mean);


