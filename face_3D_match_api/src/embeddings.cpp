#include "embeddings.h"
#include <iostream>
#include <fstream>
#include <sstream>

static cv::dnn::Net dnn_net;

bool initialize_dnn_model(const std::string& modelPath) {
    std::cout << "[DEBUG] Attempting to load DNN model from: " << modelPath << std::endl;
    try {
        dnn_net = cv::dnn::readNetFromONNX(modelPath);
        if (dnn_net.empty()) {
            std::cout << "[ERROR] DNN net is empty after loading: " << modelPath << std::endl;
            return false;
        }
        std::cout << "[INFO] OpenCV DNN model loaded successfully: " << modelPath << std::endl;
        
        // Print model info
        std::vector<std::string> layerNames = dnn_net.getLayerNames();
        std::cout << "[DEBUG] Model has " << layerNames.size() << " layers" << std::endl;
        
        return true;
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception while loading DNN model: " << e.what() << std::endl;
        return false;
    } catch (...) {
        std::cout << "[ERROR] Unknown exception while loading DNN model" << std::endl;
        return false;
    }
}

std::vector<Embedding> compute_embeddings(const std::vector<cv::Mat>& preprocessed) {
    std::vector<Embedding> out;
    std::cout << "[DEBUG] Computing embeddings for " << preprocessed.size() << " images" << std::endl;
    
    if (dnn_net.empty()) {
        std::cout << "[WARNING] DNN model not initialized, using fallback histogram method" << std::endl;
        // Fallback to histogram
        out.reserve(preprocessed.size());
        for (const auto& img : preprocessed) {
            Embedding e(128, 0.0f);
            cv::Mat gray; cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);
            int bins = 128; int histSize[] = {bins};
            float range[] = {0, 256}; const float* ranges[] = {range};
            int channels[] = {0}; cv::Mat hist;
            cv::calcHist(&gray, 1, channels, cv::Mat(), hist, 1, histSize, ranges, true, false);
            double sum = cv::sum(hist)[0] + 1e-6;
            for (int i = 0; i < bins; ++i) e[i] = static_cast<float>(hist.at<float>(i) / sum);
            out.push_back(std::move(e));
        }
        std::cout << "[DEBUG] Fallback: Generated " << out.size() << " histogram embeddings" << std::endl;
        return out;
    }

    try {
        std::cout << "[DEBUG] Using OpenCV DNN for embedding computation" << std::endl;
        out.reserve(preprocessed.size());
        for (size_t i = 0; i < preprocessed.size(); ++i) {
            const auto& img = preprocessed[i];
            std::cout << "[DEBUG] Processing image " << (i+1) << "/" << preprocessed.size() << std::endl;
            
            // Preprocess image for DNN model
            cv::Mat resized, normalized;
            cv::resize(img, resized, cv::Size(112, 112));
            resized.convertTo(normalized, CV_32F, 1.0/255.0);
            
            // Normalize to [-1, 1] range (typical for face recognition models)
            normalized = (normalized - 0.5) / 0.5;
            
            // Create blob for DNN
            cv::Mat blob = cv::dnn::blobFromImage(normalized, 1.0, cv::Size(112, 112), cv::Scalar(0, 0, 0), false, false, CV_32F);
            std::cout << "[DEBUG] Blob shape: " << blob.size << std::endl;
            
            // Run inference
            dnn_net.setInput(blob);
            cv::Mat output = dnn_net.forward();
            std::cout << "[DEBUG] Output shape: " << output.size << ", total elements: " << output.total() << std::endl;
            
            // Extract embedding (flatten the output)
            Embedding embedding;
            if (output.total() > 0) {
                embedding.assign((float*)output.data, (float*)output.data + output.total());
                std::cout << "[DEBUG] Generated embedding with " << embedding.size() << " dimensions" << std::endl;
            } else {
                std::cout << "[ERROR] DNN output is empty, using fallback" << std::endl;
                // Fallback if output is empty
                embedding.resize(512, 0.0f); // Default size for face embeddings
            }
            
            out.push_back(std::move(embedding));
        }
        std::cout << "[INFO] Successfully computed " << out.size() << " embeddings using OpenCV DNN" << std::endl;
    } catch (const std::exception& e) {
        std::cout << "[ERROR] DNN inference failed with exception: " << e.what() << std::endl;
        std::cout << "[WARNING] Falling back to histogram method" << std::endl;
        // Fallback to histogram
        out.clear();
        out.reserve(preprocessed.size());
        for (const auto& img : preprocessed) {
            Embedding e(128, 0.0f);
            cv::Mat gray; cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);
            int bins = 128; int histSize[] = {bins};
            float range[] = {0, 256}; const float* ranges[] = {range};
            int channels[] = {0}; cv::Mat hist;
            cv::calcHist(&gray, 1, channels, cv::Mat(), hist, 1, histSize, ranges, true, false);
            double sum = cv::sum(hist)[0] + 1e-6;
            for (int i = 0; i < bins; ++i) e[i] = static_cast<float>(hist.at<float>(i) / sum);
            out.push_back(std::move(e));
        }
        std::cout << "[DEBUG] Fallback: Generated " << out.size() << " histogram embeddings" << std::endl;
    } catch (...) {
        std::cout << "[ERROR] DNN inference failed with unknown exception" << std::endl;
        std::cout << "[WARNING] Falling back to histogram method" << std::endl;
        // Fallback to histogram
        out.clear();
        out.reserve(preprocessed.size());
        for (const auto& img : preprocessed) {
            Embedding e(128, 0.0f);
            cv::Mat gray; cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);
            int bins = 128; int histSize[] = {bins};
            float range[] = {0, 256}; const float* ranges[] = {range};
            int channels[] = {0}; cv::Mat hist;
            cv::calcHist(&gray, 1, channels, cv::Mat(), hist, 1, histSize, ranges, true, false);
            double sum = cv::sum(hist)[0] + 1e-6;
            for (int i = 0; i < bins; ++i) e[i] = static_cast<float>(hist.at<float>(i) / sum);
            out.push_back(std::move(e));
        }
        std::cout << "[DEBUG] Fallback: Generated " << out.size() << " histogram embeddings" << std::endl;
    }
    return out;
}

Embedding compute_mean_embedding(const std::vector<Embedding>& embs) {
    if (embs.empty()) return {};
    Embedding mean(embs[0].size(), 0.0f);
    for (const auto& e : embs) {
        for (size_t i = 0; i < e.size(); ++i) mean[i] += e[i];
    }
    for (auto& v : mean) v /= static_cast<float>(embs.size());
    return mean;
}

// Load embeddings from file system
std::vector<Embedding> load_employee_embeddings(const std::string& employeeId) {
    std::vector<Embedding> embeddings;
    std::string baseDir = "/app/employee_data/embedding/employee_" + employeeId;
    
    for (int i = 0; i < 10; ++i) {
        std::string filePath = baseDir + "/emb_" + std::to_string(i) + ".txt";
        std::ifstream file(filePath);
        if (!file.is_open()) continue;
        
        std::string line;
        if (std::getline(file, line)) {
            std::vector<float> embedding;
            std::stringstream ss(line);
            std::string value;
            
            while (std::getline(ss, value, ',')) {
                try {
                    embedding.push_back(std::stof(value));
                } catch (const std::exception& e) {
                    std::cout << "[WARNING] Failed to parse embedding value: " << value << std::endl;
                }
            }
            
            if (!embedding.empty()) {
                embeddings.push_back(embedding);
            }
        }
        file.close();
    }
    
    std::cout << "[INFO] Loaded " << embeddings.size() << " embeddings for employee " << employeeId << std::endl;
    return embeddings;
}

Embedding load_mean_embedding(const std::string& employeeId) {
    std::string filePath = "/app/employee_data/embedding/employee_" + employeeId + "/mean.txt";
    std::ifstream file(filePath);
    Embedding mean_embedding;
    
    if (!file.is_open()) {
        std::cout << "[WARNING] Mean embedding file not found: " << filePath << std::endl;
        return mean_embedding;
    }
    
    std::string line;
    if (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string value;
        
        while (std::getline(ss, value, ',')) {
            try {
                mean_embedding.push_back(std::stof(value));
            } catch (const std::exception& e) {
                std::cout << "[WARNING] Failed to parse mean embedding value: " << value << std::endl;
            }
        }
    }
    file.close();
    
    std::cout << "[INFO] Loaded mean embedding with " << mean_embedding.size() << " dimensions for employee " << employeeId << std::endl;
    return mean_embedding;
}

// Compare embeddings for face recognition
ComparisonResult compare_face_embedding(const Embedding& input_embedding, const std::string& employeeId) {
    ComparisonResult result;
    
    // Load stored embeddings
    auto stored_embeddings = load_employee_embeddings(employeeId);
    auto mean_embedding = load_mean_embedding(employeeId);
    
    if (stored_embeddings.empty() && mean_embedding.empty()) {
        result.message = "No stored embeddings found for employee " + employeeId;
        return result;
    }
    
    // Normalize input embedding
    Embedding normalized_input = input_embedding;
    float norm = 0.0f;
    for (float val : normalized_input) norm += val * val;
    norm = std::sqrt(norm);
    if (norm > 0) {
        for (float& val : normalized_input) val /= norm;
    }
    
    float best_similarity = 0.0f;
    Embedding best_match;
    
    // Compare with individual embeddings
    for (const auto& stored_emb : stored_embeddings) {
        if (stored_emb.size() != normalized_input.size()) continue;
        
        // Normalize stored embedding
        Embedding normalized_stored = stored_emb;
        float stored_norm = 0.0f;
        for (float val : normalized_stored) stored_norm += val * val;
        stored_norm = std::sqrt(stored_norm);
        if (stored_norm > 0) {
            for (float& val : normalized_stored) val /= stored_norm;
        }
        
        // Calculate cosine similarity
        float similarity = 0.0f;
        for (size_t i = 0; i < normalized_input.size(); ++i) {
            similarity += normalized_input[i] * normalized_stored[i];
        }
        
        if (similarity > best_similarity) {
            best_similarity = similarity;
            best_match = stored_emb;
        }
    }
    
    // Also compare with mean embedding if available
    if (!mean_embedding.empty() && mean_embedding.size() == normalized_input.size()) {
        Embedding normalized_mean = mean_embedding;
        float mean_norm = 0.0f;
        for (float val : normalized_mean) mean_norm += val * val;
        mean_norm = std::sqrt(mean_norm);
        if (mean_norm > 0) {
            for (float& val : normalized_mean) val /= mean_norm;
        }
        
        float mean_similarity = 0.0f;
        for (size_t i = 0; i < normalized_input.size(); ++i) {
            mean_similarity += normalized_input[i] * normalized_mean[i];
        }
        
        if (mean_similarity > best_similarity) {
            best_similarity = mean_similarity;
            best_match = mean_embedding;
        }
    }
    
    // Set threshold for matching (adjust as needed)
    const float SIMILARITY_THRESHOLD = 0.75f;
    
    result.similarity = best_similarity;
    result.match = best_similarity >= SIMILARITY_THRESHOLD;
    
    if (result.match) {
        result.message = "Face recognition successful. Similarity: " + std::to_string(best_similarity);
    } else {
        result.message = "Face recognition failed. Similarity: " + std::to_string(best_similarity) + " (threshold: " + std::to_string(SIMILARITY_THRESHOLD) + ")";
    }
    
    std::cout << "[INFO] Face comparison result: " << result.message << std::endl;
    return result;
}


