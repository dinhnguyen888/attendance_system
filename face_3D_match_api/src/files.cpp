#include "files.h"
#include <filesystem>
#include <fstream>

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


