#include "files.h"
#include <filesystem>
#include <fstream>
#include <chrono>
#include <iomanip>
#include <sstream>

static std::string ensure_dir(const std::string& base) {
    std::filesystem::create_directories(base);
    return base;
}

std::string save_video(const std::string& employeeId, const std::vector<uint8_t>& bytes) {
    std::string dir = ensure_dir("/app/employee_data/video/employee_" + employeeId);
    std::string path = dir + "/input.mp4";
    std::ofstream f(path, std::ios::binary); f.write((const char*)bytes.data(), bytes.size());
    return path;
}

std::string save_frames(const std::string& employeeId, const std::vector<cv::Mat>& frames) {
    std::string dir = ensure_dir("/app/employee_data/image/employee_" + employeeId);
    for (size_t i = 0; i < frames.size(); ++i) {
        cv::imwrite(dir + "/frame_" + std::to_string(i) + ".jpg", frames[i]);
    }
    return dir;
}

std::string save_preprocessed_frames(const std::string& employeeId, const std::vector<cv::Mat>& frames) {
    std::string dir = ensure_dir("/app/employee_data/image_preprocess/employee_" + employeeId);
    for (size_t i = 0; i < frames.size(); ++i) {
        cv::imwrite(dir + "/pre_" + std::to_string(i) + ".jpg", frames[i]);
    }
    return dir;
}

std::string save_embeddings(const std::string& employeeId, const std::vector<std::vector<float>>& embs) {
    std::string dir = ensure_dir("/app/employee_data/embedding/employee_" + employeeId);
    for (size_t i = 0; i < embs.size(); ++i) {
        std::ofstream f(dir + "/emb_" + std::to_string(i) + ".txt");
        for (size_t j = 0; j < embs[i].size(); ++j) {
            if (j) f << ",";
            f << embs[i][j];
        }
    }
    return dir;
}

bool save_mean_embedding(const std::string& employeeId, const std::vector<float>& mean) {
    std::string dir = ensure_dir("/app/employee_data/embedding/employee_" + employeeId);
    std::ofstream f(dir + "/mean.txt");
    if (!f.is_open()) return false;
    for (size_t i = 0; i < mean.size(); ++i) {
        if (i) f << ",";
        f << mean[i];
    }
    return true;
}

std::string save_comparison_image(const std::string& employeeId, const cv::Mat& image, const std::string& action) {
    std::string dir = ensure_dir("/app/employee_data/comparison/employee_" + employeeId);
    
    // Generate timestamp for unique filename
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()) % 1000;
    
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y%m%d_%H%M%S");
    ss << "_" << std::setfill('0') << std::setw(3) << ms.count();
    
    std::string filename = action + "_" + ss.str() + ".jpg";
    std::string filepath = dir + "/" + filename;
    
    cv::imwrite(filepath, image);
    return filepath;
}


