#include "video_processing.h"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <cstdio>
#include <cstdlib>

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

    cv::CascadeClassifier& cascade = get_face_cascade();
    int frameCount = 0;
    int validFrames = 0;
    
    while (frameCount < 30) { // Check first 30 frames
        cv::Mat frame;
        if (!cap.read(frame)) break;
        
        cv::Mat gray;
        cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
        
        std::vector<cv::Rect> faces;
        cascade.detectMultiScale(gray, faces, 1.1, 3, 0, cv::Size(60, 60));
        
        if (faces.size() == 1) {
            validFrames++;
        } else if (faces.size() > 1) {
            result.message = "Multiple faces detected";
            std::remove(tmpPath.c_str());
            return result;
        }
        
        frameCount++;
    }
    
    std::remove(tmpPath.c_str());
    
    if (validFrames < 5) {
        result.message = "No face or insufficient face frames";
        return result;
    }
    
    result.ok = true;
    result.message = "Video validation passed";
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

    cv::CascadeClassifier& cascade = get_face_cascade();
    for (int s = 0; s < segments; ++s) {
        double start = (total * s) / segments;
        double end = (total * (s + 1)) / segments;
        double bestScore = -1.0; cv::Mat best;

        for (double i = start; i < end; i += std::max(1.0, (end-start)/15.0)) {
            cap.set(cv::CAP_PROP_POS_FRAMES, i);
            cv::Mat frame; if (!cap.read(frame)) break;
            cv::Mat gray; cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
            std::vector<cv::Rect> faces; cascade.detectMultiScale(gray, faces, 1.1, 3, 0, cv::Size(60,60));
            if (faces.size() != 1) continue;
            // focus score: variance of Laplacian
            cv::Mat lap; cv::Laplacian(gray, lap, CV_64F);
            cv::Scalar mu, sigma; cv::meanStdDev(lap, mu, sigma);
            double score = sigma.val[0] * sigma.val[0];
            if (score > bestScore) { bestScore = score; best = frame.clone(); }
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

    cv::CascadeClassifier& cascade = get_face_cascade();
    for (int s = 0; s < segments; ++s) {
        double start = (total * s) / segments;
        double end = (total * (s + 1)) / segments;
        double bestScore = -1.0; cv::Mat best;

        for (double i = start; i < end; i += std::max(1.0, (end-start)/15.0)) {
            cap.set(cv::CAP_PROP_POS_FRAMES, i);
            cv::Mat frame; if (!cap.read(frame)) break;
            cv::Mat gray; cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
            std::vector<cv::Rect> faces; cascade.detectMultiScale(gray, faces, 1.1, 3, 0, cv::Size(60,60));
            if (faces.size() != 1) continue;
            // focus score: variance of Laplacian
            cv::Mat lap; cv::Laplacian(gray, lap, CV_64F);
            cv::Scalar mu, sigma; cv::meanStdDev(lap, mu, sigma);
            double score = sigma.val[0] * sigma.val[0];
            if (score > bestScore) { bestScore = score; best = frame.clone(); }
        }
        if (!best.empty()) result.push_back(best);
    }
    
    // Cleanup converted file
    if (actualVideoPath != videoPath) {
        std::remove(actualVideoPath.c_str());
    }
    
    return result;
}