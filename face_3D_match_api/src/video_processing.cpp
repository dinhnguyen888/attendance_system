#include "video_processing.h"
#include "face_processing.h"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <cmath>

cv::CascadeClassifier& get_face_cascade() {
    static cv::CascadeClassifier cascade;
    static bool loaded = false;
    if (!loaded) {
        if (!cascade.load("/app/cascade/haarcascade_frontalface_alt.xml")) {
            std::cout << "[ERROR] Cannot load face cascade" << std::endl;
        }
        loaded = true;
    }
    return cascade;
}

ValidationResult validate_video_faces(const std::vector<uint8_t>& videoBytes) {
    ValidationResult result;
    result.ok = false;
    
    std::string tmpPath = "/tmp/validate_video.mp4";
    FILE* f = fopen(tmpPath.c_str(), "wb");
    if (!f) {
        result.message = "Cannot create temp file";
        return result;
    }
    fwrite(videoBytes.data(), 1, videoBytes.size(), f);
    fclose(f);

    cv::VideoCapture cap(tmpPath);
    if (!cap.isOpened()) {
        result.message = "Cannot open video file";
        std::remove(tmpPath.c_str());
        return result;
    }

    int frameCount = 0;
    int validFrames = 0;
    int multipleFacesFrames = 0;
    
    while (frameCount < 30) { // Check first 30 frames
        cv::Mat frame;
        if (!cap.read(frame)) break;
        
        // Use enhanced face detection to find the largest face
        cv::Rect largest_face = detect_largest_face(frame);
        
        if (!largest_face.empty()) {
            // Check if there are multiple faces by detecting all faces
            cv::Mat gray;
            cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
            
            cv::CascadeClassifier& cascade = get_face_cascade();
            std::vector<cv::Rect> all_faces;
            cascade.detectMultiScale(gray, all_faces, 1.1, 3, 0, cv::Size(60, 60));
            
            if (all_faces.size() == 1) {
                validFrames++;
            } else if (all_faces.size() > 1) {
                multipleFacesFrames++;
                // Allow some frames with multiple faces, but not too many
                if (multipleFacesFrames > 5) {
                    result.message = "Too many frames with multiple faces detected";
                    std::remove(tmpPath.c_str());
                    return result;
                }
            }
        }
        
        frameCount++;
    }
    
    std::remove(tmpPath.c_str());
    
    if (validFrames < 5) {
        result.message = "No face or insufficient face frames";
        return result;
    }
    
    result.ok = true;
    result.message = "Video validation passed with enhanced face detection";
    return result;
}

std::vector<cv::Mat> extract_representative_frames(const std::vector<uint8_t>& videoBytes, int numSegments) {
    std::vector<cv::Mat> result;
    std::string tmpPath = "/tmp/upload_video.mp4";
    FILE* f = fopen(tmpPath.c_str(), "wb");
    if (!f) {
        std::cout << "[DEBUG] Cannot open temp file for writing" << std::endl;
        return result;
    }
    fwrite(videoBytes.data(), 1, videoBytes.size(), f);
    fclose(f);
    std::cout << "[DEBUG] Written " << videoBytes.size() << " bytes to temp file" << std::endl;

    cv::VideoCapture cap(tmpPath);
    if (!cap.isOpened()) {
        std::cout << "[DEBUG] Cannot open video file with OpenCV" << std::endl;
        return result;
    }

    double total = cap.get(cv::CAP_PROP_FRAME_COUNT);
    std::cout << "[DEBUG] Video has " << total << " frames" << std::endl;
    if (total <= 0) {
        std::cout << "[DEBUG] Invalid frame count" << std::endl;
        return result;
    }
    int segments = std::max(1, numSegments);

    for (int s = 0; s < segments; ++s) {
        double start = (total * s) / segments;
        double end = (total * (s + 1)) / segments;
        double bestScore = -1.0; cv::Mat best;

        for (double i = start; i < end; i += std::max(1.0, (end-start)/15.0)) {
            cap.set(cv::CAP_PROP_POS_FRAMES, i);
            cv::Mat frame; if (!cap.read(frame)) break;
            
            // Use enhanced face detection to find the largest face
            cv::Rect largest_face = detect_largest_face(frame);
            if (largest_face.empty()) continue;
            
            // Check if there are multiple faces
            cv::Mat gray; cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
            cv::CascadeClassifier& cascade = get_face_cascade();
            std::vector<cv::Rect> all_faces; 
            cascade.detectMultiScale(gray, all_faces, 1.1, 3, 0, cv::Size(60,60));
            if (all_faces.size() != 1) continue;
            
            // Enhanced focus score: combine Laplacian variance with face size and position
            cv::Mat lap; cv::Laplacian(gray, lap, CV_64F);
            cv::Scalar mu, sigma; cv::meanStdDev(lap, mu, sigma);
            double laplacian_score = sigma.val[0] * sigma.val[0];
            
            // Face size score (larger faces are better)
            double face_size_score = largest_face.area() / (frame.rows * frame.cols);
            
            // Face position score (center is better)
            double center_x = frame.cols / 2.0;
            double center_y = frame.rows / 2.0;
            double face_center_x = largest_face.x + largest_face.width / 2.0;
            double face_center_y = largest_face.y + largest_face.height / 2.0;
            double distance_from_center = sqrt(pow(face_center_x - center_x, 2) + pow(face_center_y - center_y, 2));
            double max_distance = sqrt(pow(frame.cols / 2.0, 2) + pow(frame.rows / 2.0, 2));
            double position_score = 1.0 - (distance_from_center / max_distance);
            
            // Combined score
            double score = laplacian_score * 0.5 + face_size_score * 1000 * 0.3 + position_score * 100 * 0.2;
            
            if (score > bestScore) { 
                bestScore = score; 
                best = frame.clone(); 
            }
        }
        if (!best.empty()) result.push_back(best);
    }
    
    // Cleanup temp file
    std::remove(tmpPath.c_str());
    
    return result;
}

std::vector<cv::Mat> extract_representative_frames_from_file(const std::string& videoPath, int numSegments) {
    std::vector<cv::Mat> result;
    
    // First try to convert with FFmpeg if OpenCV fails
    std::string convertedPath = videoPath + "_converted.mp4";
    std::string cmd = "ffmpeg -i \"" + videoPath + "\" -c:v libx264 -preset fast -y \"" + convertedPath + "\" 2>/dev/null";
    int ret = system(cmd.c_str());
    
    std::string actualVideoPath = videoPath;
    if (ret == 0) {
        actualVideoPath = convertedPath;
        std::cout << "[DEBUG] Converted video with FFmpeg" << std::endl;
    }
    
    cv::VideoCapture cap(actualVideoPath);
    if (!cap.isOpened()) {
        std::cout << "[DEBUG] Cannot open video file: " << actualVideoPath << std::endl;
        return result;
    }

    double total = cap.get(cv::CAP_PROP_FRAME_COUNT);
    std::cout << "[DEBUG] Video has " << total << " frames" << std::endl;
    if (total <= 0) {
        std::cout << "[DEBUG] Invalid frame count" << std::endl;
        return result;
    }
    int segments = std::max(1, numSegments);

    for (int s = 0; s < segments; ++s) {
        double start = (total * s) / segments;
        double end = (total * (s + 1)) / segments;
        double bestScore = -1.0; cv::Mat best;

        for (double i = start; i < end; i += std::max(1.0, (end-start)/15.0)) {
            cap.set(cv::CAP_PROP_POS_FRAMES, i);
            cv::Mat frame; if (!cap.read(frame)) break;
            
            // Use enhanced face detection to find the largest face
            cv::Rect largest_face = detect_largest_face(frame);
            if (largest_face.empty()) continue;
            
            // Check if there are multiple faces
            cv::Mat gray; cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
            cv::CascadeClassifier& cascade = get_face_cascade();
            std::vector<cv::Rect> all_faces; 
            cascade.detectMultiScale(gray, all_faces, 1.1, 3, 0, cv::Size(60,60));
            if (all_faces.size() != 1) continue;
            
            // Enhanced focus score: combine Laplacian variance with face size and position
            cv::Mat lap; cv::Laplacian(gray, lap, CV_64F);
            cv::Scalar mu, sigma; cv::meanStdDev(lap, mu, sigma);
            double laplacian_score = sigma.val[0] * sigma.val[0];
            
            // Face size score (larger faces are better)
            double face_size_score = largest_face.area() / (frame.rows * frame.cols);
            
            // Face position score (center is better)
            double center_x = frame.cols / 2.0;
            double center_y = frame.rows / 2.0;
            double face_center_x = largest_face.x + largest_face.width / 2.0;
            double face_center_y = largest_face.y + largest_face.height / 2.0;
            double distance_from_center = sqrt(pow(face_center_x - center_x, 2) + pow(face_center_y - center_y, 2));
            double max_distance = sqrt(pow(frame.cols / 2.0, 2) + pow(frame.rows / 2.0, 2));
            double position_score = 1.0 - (distance_from_center / max_distance);
            
            // Combined score
            double score = laplacian_score * 0.5 + face_size_score * 1000 * 0.3 + position_score * 100 * 0.2;
            
            if (score > bestScore) { 
                bestScore = score; 
                best = frame.clone(); 
            }
        }
        if (!best.empty()) result.push_back(best);
    }
    
    // Cleanup converted file
    if (actualVideoPath != videoPath) {
        std::remove(actualVideoPath.c_str());
    }
    
    return result;
}