#pragma once
#include <opencv2/opencv.hpp>
#include <vector>

using Embedding = std::vector<float>;

// Initialize OpenCV DNN model
bool initialize_dnn_model(const std::string& modelPath);

// Compute embeddings using OpenCV DNN
std::vector<Embedding> compute_embeddings(const std::vector<cv::Mat>& preprocessed);
Embedding compute_mean_embedding(const std::vector<Embedding>& embs);


