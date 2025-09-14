#include "face_processing.h"
#include <iostream>
#include <algorithm>

// Get face cascade classifier (reuse from video_processing)
static cv::CascadeClassifier& get_face_cascade() {
    static cv::CascadeClassifier cascade;
    static bool loaded = false;
    if (!loaded) {
        if (!cascade.load("/app/cascade/haarcascade_frontalface_alt.xml")) {
            std::cout << "[ERROR] Cannot load face cascade in face_processing" << std::endl;
        }
        loaded = true;
    }
    return cascade;
}

static cv::Mat skin_normalize(const cv::Mat& img) {
    cv::Mat ycrcb; cv::cvtColor(img, ycrcb, cv::COLOR_BGR2YCrCb);
    std::vector<cv::Mat> ch; cv::split(ycrcb, ch);
    cv::equalizeHist(ch[0], ch[0]);
    cv::merge(ch, ycrcb);
    cv::Mat out; cv::cvtColor(ycrcb, out, cv::COLOR_YCrCb2BGR);
    return out;
}

// Detect the largest face in the frame (closest to camera)
cv::Rect detect_largest_face(const cv::Mat& frame) {
    cv::Mat gray;
    cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
    
    cv::CascadeClassifier& cascade = get_face_cascade();
    std::vector<cv::Rect> faces;
    cascade.detectMultiScale(gray, faces, 1.1, 3, 0, cv::Size(60, 60));
    
    if (faces.empty()) {
        return cv::Rect();
    }
    
    // Find the largest face (closest to camera)
    auto largest_face = std::max_element(faces.begin(), faces.end(),
        [](const cv::Rect& a, const cv::Rect& b) {
            return a.area() < b.area();
        });
    
    return *largest_face;
}

// Crop face from frame and enhance it - tighter crop to avoid shoulders
cv::Mat crop_and_enhance_face(const cv::Mat& frame, const cv::Rect& face_rect) {
    if (face_rect.empty()) {
        return cv::Mat();
    }
    
    // Calculate tighter padding - focus on face area only
    // Use smaller padding to avoid cutting shoulders
    int face_size = std::min(face_rect.width, face_rect.height);
    int padding = std::max(10, face_size / 8); // Much smaller padding
    
    // Adjust padding to be asymmetric - more padding on top, less on bottom
    int top_padding = padding * 1.5;    // More space above head
    int side_padding = padding;         // Normal side padding
    int bottom_padding = padding / 2;   // Minimal padding below chin
    
    cv::Rect tight_rect(
        std::max(0, face_rect.x - side_padding),
        std::max(0, face_rect.y - top_padding),
        std::min(frame.cols - std::max(0, face_rect.x - side_padding), 
                 face_rect.width + 2 * side_padding),
        std::min(frame.rows - std::max(0, face_rect.y - top_padding), 
                 face_rect.height + top_padding + bottom_padding)
    );
    
    cv::Mat cropped_face = frame(tight_rect);
    
    // Enhance the cropped face
    cv::Mat enhanced = enhance_image_quality(cropped_face);
    
    // Resize to standard size for face recognition
    cv::Mat resized;
    cv::resize(enhanced, resized, cv::Size(112, 112));
    
    return resized;
}

// Enhance image quality using multiple techniques
cv::Mat enhance_image_quality(const cv::Mat& img) {
    if (img.empty()) return img;
    
    cv::Mat enhanced = img.clone();
    
    // Step 1: Denoise
    enhanced = denoise_image(enhanced);
    
    // Step 2: Apply super resolution if image is small
    if (enhanced.rows < 200 || enhanced.cols < 200) {
        enhanced = apply_super_resolution(enhanced);
    }
    
    // Step 3: Sharpen
    enhanced = sharpen_image(enhanced);
    
    // Step 4: Skin normalization
    enhanced = skin_normalize(enhanced);
    
    return enhanced;
}

// Apply super resolution using bicubic interpolation with enhancement
cv::Mat apply_super_resolution(const cv::Mat& img) {
    if (img.empty()) return img;
    
    cv::Mat upscaled;
    cv::resize(img, upscaled, cv::Size(img.cols * 2, img.rows * 2), 0, 0, cv::INTER_CUBIC);
    
    // Apply edge-preserving filter to reduce artifacts
    cv::Mat filtered;
    cv::edgePreservingFilter(upscaled, filtered, 1, 0.4, 0.1);
    
    return filtered;
}

// Denoise image using Non-local Means Denoising
cv::Mat denoise_image(const cv::Mat& img) {
    if (img.empty()) return img;
    
    cv::Mat denoised;
    
    // Convert to LAB color space for better denoising
    cv::Mat lab;
    cv::cvtColor(img, lab, cv::COLOR_BGR2Lab);
    
    std::vector<cv::Mat> channels;
    cv::split(lab, channels);
    
    // Denoise each channel
    for (auto& channel : channels) {
        cv::fastNlMeansDenoising(channel, channel, 3, 7, 21);
    }
    
    cv::merge(channels, lab);
    cv::cvtColor(lab, denoised, cv::COLOR_Lab2BGR);
    
    return denoised;
}

// Sharpen image using unsharp mask
cv::Mat sharpen_image(const cv::Mat& img) {
    if (img.empty()) return img;
    
    cv::Mat blurred, sharpened;
    
    // Create Gaussian blur
    cv::GaussianBlur(img, blurred, cv::Size(0, 0), 3);
    
    // Apply unsharp mask
    cv::addWeighted(img, 1.5, blurred, -0.5, 0, sharpened);
    
    return sharpened;
}

// Enhanced preprocessing function with face detection and quality improvement
std::vector<cv::Mat> preprocess_faces(const std::vector<cv::Mat>& frames) {
    std::vector<cv::Mat> out;
    out.reserve(frames.size());
    
    for (const auto& frame : frames) {
        if (frame.empty()) continue;
        
        // Try ArcFace pipeline first
        ArcFaceResult arcface_result = process_face_with_arcface(frame);
        if (arcface_result.success && !arcface_result.aligned_face.empty()) {
            out.push_back(arcface_result.aligned_face);
            std::cout << "[DEBUG] ArcFace processed face: " << arcface_result.aligned_face.size() << std::endl;
            continue;
        }
        
        // Fallback to legacy processing
        std::cout << "[DEBUG] Using legacy face processing" << std::endl;
        cv::Rect face_rect = detect_largest_face(frame);
        
        if (face_rect.empty()) {
            std::cout << "[WARNING] No face detected in frame, using original preprocessing" << std::endl;
            // Fallback to original method
            cv::Mat resized; cv::resize(frame, resized, cv::Size(112, 112));
            cv::Mat normed = skin_normalize(resized);
            out.push_back(normed);
            continue;
        }
        
        // Crop and enhance the face
        cv::Mat enhanced_face = crop_and_enhance_face(frame, face_rect);
        
        if (!enhanced_face.empty()) {
            out.push_back(enhanced_face);
            std::cout << "[DEBUG] Enhanced face processed: " << enhanced_face.size() << std::endl;
        } else {
            std::cout << "[WARNING] Failed to enhance face, using original preprocessing" << std::endl;
            // Fallback to original method
            cv::Mat resized; cv::resize(frame, resized, cv::Size(112, 112));
            cv::Mat normed = skin_normalize(resized);
            out.push_back(normed);
        }
    }
    
    std::cout << "[INFO] Enhanced preprocessing completed: " << out.size() << " faces processed" << std::endl;
    return out;
}


