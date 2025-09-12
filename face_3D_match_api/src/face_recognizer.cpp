#include "face_recognizer.h"
#include <opencv2/opencv.hpp>
#include <vector>
#include <string>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <chrono>
#include <memory>

#include "face_recognizer.h"
#include "common.h"
#include "face_detector.h"

FaceRecognizer::FaceRecognizer() : initialized_(false) {
    face_detector_ = std::make_unique<FaceDetector>();
    arcface_model_ = std::make_unique<ArcFaceModel>();
}

FaceRecognizer::~FaceRecognizer() {}

bool FaceRecognizer::initialize(const std::string& arcface_model_path) {
    try {
        if (!face_detector_->initialize()) {
            std::cerr << "Failed to initialize face detector" << std::endl;
            return false;
        }
        
        if (!arcface_model_->initialize(arcface_model_path)) {
            std::cerr << "Failed to initialize ArcFace model" << std::endl;
            return false;
        }
        
        // Load existing employee data
        loadEmployeeData();
        
        initialized_ = true;
        std::cout << "Face recognizer initialized successfully" << std::endl;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Face recognizer initialization error: " << e.what() << std::endl;
        return false;
    }
}

std::vector<FaceEmbedding> FaceRecognizer::processVideo(const std::string& video_path, int total_frames) {
    std::vector<FaceEmbedding> embeddings;
    
    if (!initialized_) {
        std::cerr << "Face recognizer not initialized" << std::endl;
        return embeddings;
    }
    
    try {
        // Extract frames from video with specified total frames
        std::vector<cv::Mat> frames = extractFramesFromVideo(video_path, total_frames);
        if (frames.empty()) {
            std::cerr << "No frames extracted from video" << std::endl;
            return embeddings;
        }
        
        // Process faces in frames
        embeddings = processFacesInFrames(frames);
        
        std::cout << "Processed video: " << frames.size() << " frames, " 
                  << embeddings.size() << " face embeddings extracted" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Video processing error: " << e.what() << std::endl;
    }
    
    return embeddings;
}

std::vector<FaceEmbedding> FaceRecognizer::processVideoFromBuffer(const std::vector<uint8_t>& video_buffer, int total_frames) {
    std::vector<FaceEmbedding> embeddings;
    
    if (!initialized_) {
        std::cerr << "Face recognizer not initialized" << std::endl;
        return embeddings;
    }
    
    try {
        // Extract frames from video buffer with specified total frames
        std::vector<cv::Mat> frames = extractFramesFromBuffer(video_buffer, total_frames);
        if (frames.empty()) {
            std::cerr << "No frames extracted from video buffer" << std::endl;
            return embeddings;
        }
        
        // Process faces in frames
        embeddings = processFacesInFrames(frames);
        
        std::cout << "Processed video buffer: " << frames.size() << " frames, " 
                  << embeddings.size() << " face embeddings extracted" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Video buffer processing error: " << e.what() << std::endl;
    }
    
    return embeddings;
}

bool FaceRecognizer::registerEmployee(const std::string& employee_id, const std::vector<FaceEmbedding>& embeddings) {
    if (!initialized_ || embeddings.empty()) {
        return false;
    }
    
    try {
        Employee employee(employee_id);
        employee.embeddings = embeddings;
        employee.created_at = getCurrentTimestamp();
        
        // Limit number of embeddings per employee
        if (employee.embeddings.size() > MAX_EMBEDDINGS_PER_EMPLOYEE) {
            employee.embeddings.resize(MAX_EMBEDDINGS_PER_EMPLOYEE);
        }
        
        employee_database_[employee_id] = employee;
        
        // Save to persistent storage
        if (saveEmployeeData(employee_id, embeddings)) {
            std::cout << "Employee " << employee_id << " registered successfully with " 
                      << embeddings.size() << " embeddings" << std::endl;
            return true;
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Employee registration error: " << e.what() << std::endl;
    }
    
    return false;
}

ComparisonResult FaceRecognizer::verifyEmployee(const std::vector<FaceEmbedding>& query_embeddings) {
    if (!initialized_ || query_embeddings.empty()) {
        return ComparisonResult(false, 0.0f, "", "System not initialized or no embeddings provided");
    }
    
    try {
        return findBestMatch(query_embeddings);
    } catch (const std::exception& e) {
        std::cerr << "Employee verification error: " << e.what() << std::endl;
        return ComparisonResult(false, 0.0f, "", "Verification error: " + std::string(e.what()));
    }
}

std::vector<cv::Mat> FaceRecognizer::extractFramesFromVideo(const std::string& video_path, int total_frames) {
    std::vector<cv::Mat> frames;
    
    try {
        cv::VideoCapture cap(video_path);
        if (!cap.isOpened()) {
            std::cerr << "Cannot open video file: " << video_path << std::endl;
            return frames;
        }
        
        // Calculate frame interval based on desired total frames
        int total_video_frames = static_cast<int>(cap.get(cv::CAP_PROP_FRAME_COUNT));
        int frame_interval = std::max(1, total_video_frames / total_frames);
        
        cv::Mat frame;
        int frames_extracted = 0;
        
        // Extract frames at regular intervals
        for (int i = 0; i < total_video_frames && frames_extracted < total_frames; i++) {
            if (i % frame_interval == 0) {
                cap.set(cv::CAP_PROP_POS_FRAMES, i);
                if (cap.read(frame)) {
                    frames.push_back(frame.clone());
                    frames_extracted++;
                }
            }
        }
        
        // If we didn't get enough frames, try to get more from the end
        if (frames_extracted < total_frames && !frames.empty() && total_video_frames > 0) {
            int remaining = total_frames - frames_extracted;
            int step = std::max(1, (total_video_frames - 1) / (remaining + 1));
            
            for (int i = total_video_frames - 1; i >= 0 && remaining > 0; i -= step) {
                cap.set(cv::CAP_PROP_POS_FRAMES, i);
                if (cap.read(frame)) {
                    frames.push_back(frame.clone());
                    remaining--;
                }
            }
        }
        
        cap.release();
        
    } catch (const std::exception& e) {
        std::cerr << "Frame extraction error: " << e.what() << std::endl;
    }
    
    return frames;
}

std::vector<cv::Mat> FaceRecognizer::extractFramesFromBuffer(const std::vector<uint8_t>& video_buffer, int total_frames) {
    std::vector<cv::Mat> frames;
    
    try {
        // Create a temporary file with a unique name
        std::string temp_dir = "/tmp";
        std::string temp_path = temp_dir + "/temp_video_" + std::to_string(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count()) + ".mp4";
        
        // Ensure the directory exists
        createDirectoryIfNotExists(temp_dir);
        
        // Write buffer to temporary file
        std::ofstream temp_file(temp_path, std::ios::binary);
        if (!temp_file) {
            std::cerr << "Failed to create temporary file: " << temp_path << std::endl;
            return frames;
        }
        
        temp_file.write(reinterpret_cast<const char*>(video_buffer.data()), video_buffer.size());
        temp_file.close();
        
        // Extract frames from temporary file
        frames = extractFramesFromVideo(temp_path, total_frames);
        
        // Clean up temporary file
        try {
            std::filesystem::remove(temp_path);
        } catch (const std::exception& e) {
            std::cerr << "Warning: Failed to remove temporary file " << temp_path 
                     << ": " << e.what() << std::endl;
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Buffer frame extraction error: " << e.what() << std::endl;
    }
    
    return frames;
}

std::vector<FaceEmbedding> FaceRecognizer::processFacesInFrames(const std::vector<cv::Mat>& frames) {
    std::vector<FaceEmbedding> embeddings;
    
    for (const auto& frame : frames) {
        // Convert to grayscale for Canny edge detection
        cv::Mat gray;
        cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
        
        // Apply Canny edge detection
        cv::Mat edges;
        cv::Canny(gray, edges, 100, 200);
        
        // Find contours
        std::vector<std::vector<cv::Point>> contours;
        cv::findContours(edges, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);
        
        // Find the largest contour (face)
        if (!contours.empty()) {
            auto largest_contour = std::max_element(contours.begin(), contours.end(),
                [](const std::vector<cv::Point>& a, const std::vector<cv::Point>& b) {
                    return cv::contourArea(a) < cv::contourArea(b);
                });
                
            // Create a mask from the largest contour
            cv::Mat mask = cv::Mat::zeros(frame.size(), CV_8UC1);
            cv::drawContours(mask, std::vector<std::vector<cv::Point>>{*largest_contour}, -1, 255, cv::FILLED);
            
            // Apply mask to original frame
            cv::Mat masked_frame;
            frame.copyTo(masked_frame, mask);
            
            // Detect faces in the masked frame
            std::vector<cv::Rect> faces = face_detector_->detectFaces(masked_frame);
            
            for (const auto& face_rect : faces) {
                // Extract face region
                cv::Mat face_roi = masked_frame(face_rect).clone();
                
                // Save the processed face image
                std::string employee_dir = "data/employee_" + std::to_string(embeddings.size() + 1);
                createDirectoryIfNotExists(employee_dir + "/picture");
                createDirectoryIfNotExists(employee_dir + "/embedding");
                
                std::string timestamp = std::to_string(std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::system_clock::now().time_since_epoch()).count());
                
                std::string image_path = employee_dir + "/picture/face_" + timestamp + ".jpg";
                cv::imwrite(image_path, face_roi);
                
                // Get face embedding
                std::vector<float> embedding = arcface_model_->extractEmbedding(face_roi);
                
                if (!embedding.empty()) {
                    // Save embedding to file
                    std::string embedding_path = employee_dir + "/embedding/embedding_" + timestamp + ".bin";
                    std::ofstream out(embedding_path, std::ios::binary);
                    out.write(reinterpret_cast<const char*>(embedding.data()), 
                             embedding.size() * sizeof(float));
                    out.close();
                    
                    FaceEmbedding face_embedding;
                    face_embedding.features = embedding;
                    face_embedding.bbox = face_rect;
                    face_embedding.confidence = 1.0f;  // Default confidence
                    
                    embeddings.push_back(face_embedding);
                }
            }
        }
    }
    
    return embeddings;
}

float FaceRecognizer::compareEmbeddings(const std::vector<float>& embedding1, const std::vector<float>& embedding2) {
    return arcface_model_->calculateSimilarity(embedding1, embedding2);
}

ComparisonResult FaceRecognizer::findBestMatch(const std::vector<FaceEmbedding>& query_embeddings) {
    float best_similarity = 0.0f;
    std::string best_employee_id;
    
    for (const auto& [employee_id, employee] : employee_database_) {
        float max_similarity_for_employee = 0.0f;
        
        // Compare each query embedding with each stored embedding
        for (const auto& query_emb : query_embeddings) {
            for (const auto& stored_emb : employee.embeddings) {
                float similarity = compareEmbeddings(query_emb.features, stored_emb.features);
                max_similarity_for_employee = std::max(max_similarity_for_employee, similarity);
            }
        }
        
        if (max_similarity_for_employee > best_similarity) {
            best_similarity = max_similarity_for_employee;
            best_employee_id = employee_id;
        }
    }
    
    bool match = best_similarity >= SIMILARITY_THRESHOLD;
    std::string message = match ? 
        "Match found with confidence " + std::to_string(best_similarity) :
        "No match found. Best similarity: " + std::to_string(best_similarity);
    
    return ComparisonResult(match, best_similarity, best_employee_id, message);
}

bool FaceRecognizer::saveEmployeeData(const std::string& employee_id, const std::vector<FaceEmbedding>& embeddings) {
    try {
        std::string data_dir = "employee_data";
        createDirectoryIfNotExists(data_dir);
        
        std::string file_path = data_dir + "/" + employee_id + ".dat";
        std::ofstream file(file_path, std::ios::binary);
        
        if (!file.is_open()) {
            std::cerr << "Cannot create employee data file: " << file_path << std::endl;
            return false;
        }
        
        // Write number of embeddings
        size_t num_embeddings = embeddings.size();
        file.write(reinterpret_cast<const char*>(&num_embeddings), sizeof(num_embeddings));
        
        // Write each embedding
        for (const auto& embedding : embeddings) {
            size_t feature_size = embedding.features.size();
            file.write(reinterpret_cast<const char*>(&feature_size), sizeof(feature_size));
            file.write(reinterpret_cast<const char*>(embedding.features.data()), 
                      feature_size * sizeof(float));
            file.write(reinterpret_cast<const char*>(&embedding.bbox), sizeof(cv::Rect));
            file.write(reinterpret_cast<const char*>(&embedding.confidence), sizeof(float));
        }
        
        file.close();
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "Save employee data error: " << e.what() << std::endl;
        return false;
    }
}

bool FaceRecognizer::loadEmployeeData() {
    try {
        std::string data_dir = "employee_data";
        if (!std::filesystem::exists(data_dir)) {
            std::cout << "Employee data directory not found. Starting with empty database." << std::endl;
            return true;
        }
        
        for (const auto& entry : std::filesystem::directory_iterator(data_dir)) {
            if (entry.path().extension() == ".dat") {
                std::string employee_id = entry.path().stem().string();
                std::ifstream file(entry.path(), std::ios::binary);
                
                if (!file.is_open()) continue;
                
                Employee employee(employee_id);
                
                // Read number of embeddings
                size_t num_embeddings;
                file.read(reinterpret_cast<char*>(&num_embeddings), sizeof(num_embeddings));
                
                // Read each embedding
                for (size_t i = 0; i < num_embeddings; ++i) {
                    size_t feature_size;
                    file.read(reinterpret_cast<char*>(&feature_size), sizeof(feature_size));
                    
                    std::vector<float> features(feature_size);
                    file.read(reinterpret_cast<char*>(features.data()), 
                             feature_size * sizeof(float));
                    
                    cv::Rect bbox;
                    float confidence;
                    file.read(reinterpret_cast<char*>(&bbox), sizeof(cv::Rect));
                    file.read(reinterpret_cast<char*>(&confidence), sizeof(float));
                    
                    employee.embeddings.emplace_back(features, bbox, confidence);
                }
                
                employee_database_[employee_id] = employee;
                file.close();
            }
        }
        
        std::cout << "Loaded " << employee_database_.size() << " employees from database" << std::endl;
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "Load employee data error: " << e.what() << std::endl;
        return false;
    }
}

std::string FaceRecognizer::getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    return ss.str();
}

bool FaceRecognizer::createDirectoryIfNotExists(const std::string& path) {
    try {
        if (!std::filesystem::exists(path)) {
            return std::filesystem::create_directories(path);
        }
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Directory creation error: " << e.what() << std::endl;
        return false;
    }
}
