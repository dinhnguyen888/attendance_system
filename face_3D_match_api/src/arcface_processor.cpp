#include "arcface_processor.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cmath>

ArcFaceProcessor::ArcFaceProcessor() 
    : initialized_(false), input_size_(112, 112), 
      mean_(cv::Scalar(127.5, 127.5, 127.5)), 
      std_(cv::Scalar(127.5, 127.5, 127.5)) {
    
    face_detector_ = std::make_unique<FaceDetector>();
    fallback_detector_ = std::make_unique<MTCNNFaceDetector>();
    face_aligner_ = std::make_unique<FaceAlignment>();
}

ArcFaceProcessor::~ArcFaceProcessor() {}

bool ArcFaceProcessor::initialize(const std::string& arcface_model_path, 
                                 const std::string& detector_model_path) {
    try {
        std::cout << "[INFO] Initializing ArcFace processor..." << std::endl;
        
        // Initialize face detector (try RetinaFace first, fallback to MTCNN)
        bool detector_ok = face_detector_->initialize(detector_model_path);
        if (!detector_ok) {
            std::cout << "[WARNING] Primary detector failed, using fallback MTCNN detector" << std::endl;
            detector_ok = fallback_detector_->initialize();
        }
        
        if (!detector_ok) {
            std::cout << "[ERROR] All face detectors failed to initialize" << std::endl;
            return false;
        }
        
        // Initialize ArcFace model
        arcface_net_ = cv::dnn::readNetFromONNX(arcface_model_path);
        if (arcface_net_.empty()) {
            std::cout << "[ERROR] Failed to load ArcFace model: " << arcface_model_path << std::endl;
            return false;
        }
        
        // Set backend and target
        arcface_net_.setPreferableBackend(cv::dnn::DNN_BACKEND_OPENCV);
        arcface_net_.setPreferableTarget(cv::dnn::DNN_TARGET_CPU);
        
        initialized_ = true;
        std::cout << "[INFO] ArcFace processor initialized successfully" << std::endl;
        return true;
        
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception initializing ArcFace processor: " << e.what() << std::endl;
        return false;
    }
}

ArcFaceResult ArcFaceProcessor::process_face(const cv::Mat& image, bool return_largest_face) {
    ArcFaceResult result;
    result.success = false;
    result.confidence = 0.0f;
    
    if (!initialized_ || image.empty()) {
        result.message = "Processor not initialized or empty image";
        return result;
    }
    
    try {
        // Step 1: Face Detection
        std::vector<FaceDetection> detections;
        
        // Try primary detector first
        if (face_detector_) {
            detections = face_detector_->detect_faces(image, 0.8f);
        }
        
        // Fallback to MTCNN if no faces found
        if (detections.empty() && fallback_detector_) {
            std::cout << "[DEBUG] Using fallback detector" << std::endl;
            detections = fallback_detector_->detect_faces(image, 0.7f);
        }
        
        if (detections.empty()) {
            result.message = "No face detected in image";
            return result;
        }
        
        // Select face (largest if multiple)
        FaceDetection selected_face = detections[0];
        if (return_largest_face && detections.size() > 1) {
            auto largest = std::max_element(detections.begin(), detections.end(),
                [](const FaceDetection& a, const FaceDetection& b) {
                    return a.bbox.area() < b.bbox.area();
                });
            selected_face = *largest;
        }
        
        std::cout << "[DEBUG] Selected face with confidence: " << selected_face.confidence << std::endl;
        
        // Step 2: Face Alignment
        if (selected_face.landmarks.size() != 5) {
            result.message = "Invalid landmarks for face alignment";
            return result;
        }
        
        cv::Mat aligned_face = face_aligner_->align_face(image, selected_face.landmarks, input_size_);
        if (aligned_face.empty()) {
            result.message = "Face alignment failed";
            return result;
        }
        
        result.aligned_face = aligned_face.clone(); // For debugging
        
        // Step 3: Extract Embedding
        std::vector<float> embedding = extract_embedding(aligned_face);
        if (embedding.empty()) {
            result.message = "Embedding extraction failed";
            return result;
        }
        
        // Step 4: Normalize Embedding
        embedding = normalize_embedding(embedding);
        
        result.success = true;
        result.embedding = embedding;
        result.confidence = selected_face.confidence;
        result.message = "Face processed successfully";
        
        std::cout << "[INFO] Face processed successfully, embedding size: " << embedding.size() << std::endl;
        
    } catch (const std::exception& e) {
        result.message = "Exception during face processing: " + std::string(e.what());
        std::cout << "[ERROR] " << result.message << std::endl;
    }
    
    return result;
}

std::vector<float> ArcFaceProcessor::extract_embedding(const cv::Mat& aligned_face) {
    std::vector<float> embedding;
    
    if (!initialized_ || aligned_face.empty()) {
        return embedding;
    }
    
    try {
        // Preprocess for ArcFace
        cv::Mat preprocessed = preprocess_for_arcface(aligned_face);
        
        // Forward pass
        arcface_net_.setInput(preprocessed);
        cv::Mat output = arcface_net_.forward();
        
        // Post-process
        embedding = postprocess_embedding(output);
        
        std::cout << "[DEBUG] Extracted embedding with " << embedding.size() << " dimensions" << std::endl;
        
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception extracting embedding: " << e.what() << std::endl;
    }
    
    return embedding;
}

cv::Mat ArcFaceProcessor::preprocess_for_arcface(const cv::Mat& aligned_face) {
    cv::Mat preprocessed;
    
    // Ensure correct size
    if (aligned_face.size() != input_size_) {
        cv::resize(aligned_face, preprocessed, input_size_);
    } else {
        preprocessed = aligned_face.clone();
    }
    
    // Convert to float and normalize to [0, 1]
    preprocessed.convertTo(preprocessed, CV_32F, 1.0/255.0);
    
    // Normalize to [-1, 1] range (standard for ArcFace)
    preprocessed = (preprocessed - 0.5) / 0.5;
    
    // Create blob (NCHW format)
    cv::Mat blob = cv::dnn::blobFromImage(preprocessed, 1.0, input_size_, 
                                         cv::Scalar(0, 0, 0), false, false, CV_32F);
    
    return blob;
}

std::vector<float> ArcFaceProcessor::postprocess_embedding(const cv::Mat& net_output) {
    std::vector<float> embedding;
    
    if (net_output.empty() || net_output.total() == 0) {
        return embedding;
    }
    
    // Flatten the output
    cv::Mat flattened = net_output.reshape(1, net_output.total());
    embedding.assign((float*)flattened.data, (float*)flattened.data + flattened.total());
    
    return embedding;
}

std::vector<float> ArcFaceProcessor::normalize_embedding(const std::vector<float>& embedding) {
    if (embedding.empty()) {
        return embedding;
    }
    
    // L2 normalization
    float norm = 0.0f;
    for (float val : embedding) {
        norm += val * val;
    }
    norm = std::sqrt(norm);
    
    if (norm < 1e-6f) {
        return embedding; // Avoid division by zero
    }
    
    std::vector<float> normalized(embedding.size());
    for (size_t i = 0; i < embedding.size(); ++i) {
        normalized[i] = embedding[i] / norm;
    }
    
    return normalized;
}

float ArcFaceProcessor::calculate_similarity(const std::vector<float>& embedding1, 
                                           const std::vector<float>& embedding2) {
    if (embedding1.size() != embedding2.size() || embedding1.empty()) {
        return 0.0f;
    }
    
    // Cosine similarity (embeddings should already be L2 normalized)
    float dot_product = 0.0f;
    for (size_t i = 0; i < embedding1.size(); ++i) {
        dot_product += embedding1[i] * embedding2[i];
    }
    
    // Clamp to [-1, 1] range to handle numerical errors
    return std::max(-1.0f, std::min(1.0f, dot_product));
}

FaceMatchResult ArcFaceProcessor::match_face(const std::vector<float>& input_embedding, 
                                           const std::string& employee_id,
                                           float threshold) {
    FaceMatchResult result;
    result.match = false;
    result.similarity = 0.0f;
    result.confidence = 0.0f;
    
    try {
        // Load stored embeddings for employee
        auto stored_embeddings = load_employee_embeddings(employee_id);
        
        if (stored_embeddings.empty()) {
            result.message = "No stored embeddings found for employee " + employee_id;
            return result;
        }
        
        // Find best match
        float best_similarity = -1.0f;
        for (const auto& stored_embedding : stored_embeddings) {
            float similarity = calculate_similarity(input_embedding, stored_embedding);
            if (similarity > best_similarity) {
                best_similarity = similarity;
            }
        }
        
        result.similarity = best_similarity;
        result.best_match_id = employee_id;
        result.match = best_similarity >= threshold;
        result.confidence = best_similarity;
        
        if (result.match) {
            result.message = "Face match successful. Similarity: " + std::to_string(best_similarity);
        } else {
            result.message = "Face match failed. Similarity: " + std::to_string(best_similarity) + 
                           " (threshold: " + std::to_string(threshold) + ")";
        }
        
        std::cout << "[INFO] " << result.message << std::endl;
        
    } catch (const std::exception& e) {
        result.message = "Exception during face matching: " + std::string(e.what());
        std::cout << "[ERROR] " << result.message << std::endl;
    }
    
    return result;
}

std::vector<ArcFaceResult> ArcFaceProcessor::process_multiple_faces(const cv::Mat& image) {
    std::vector<ArcFaceResult> results;
    
    if (!initialized_ || image.empty()) {
        return results;
    }
    
    try {
        // Detect all faces
        std::vector<FaceDetection> detections;
        
        if (face_detector_) {
            detections = face_detector_->detect_faces(image, 0.8f);
        }
        
        if (detections.empty() && fallback_detector_) {
            detections = fallback_detector_->detect_faces(image, 0.7f);
        }
        
        // Process each face
        for (const auto& detection : detections) {
            ArcFaceResult result;
            result.success = false;
            
            if (detection.landmarks.size() == 5) {
                cv::Mat aligned_face = face_aligner_->align_face(image, detection.landmarks, input_size_);
                if (!aligned_face.empty()) {
                    std::vector<float> embedding = extract_embedding(aligned_face);
                    if (!embedding.empty()) {
                        result.success = true;
                        result.embedding = normalize_embedding(embedding);
                        result.confidence = detection.confidence;
                        result.aligned_face = aligned_face.clone();
                        result.message = "Face processed successfully";
                    }
                }
            }
            
            if (!result.success) {
                result.message = "Failed to process face";
            }
            
            results.push_back(result);
        }
        
        std::cout << "[INFO] Processed " << results.size() << " faces from image" << std::endl;
        
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception processing multiple faces: " << e.what() << std::endl;
    }
    
    return results;
}

std::vector<std::vector<float>> ArcFaceProcessor::load_employee_embeddings(const std::string& employee_id) {
    std::vector<std::vector<float>> embeddings;
    std::string base_dir = "/app/employee_data/embeddings/employee_" + employee_id;
    
    // Try to load multiple embeddings
    for (int i = 0; i < 10; ++i) {
        std::string file_path = base_dir + "/emb_" + std::to_string(i) + ".txt";
        auto embedding = load_embedding(file_path);
        if (!embedding.empty()) {
            embeddings.push_back(embedding);
        }
    }
    
    // Also try to load mean embedding
    std::string mean_path = base_dir + "/mean.txt";
    auto mean_embedding = load_embedding(mean_path);
    if (!mean_embedding.empty()) {
        embeddings.push_back(mean_embedding);
    }
    
    std::cout << "[INFO] Loaded " << embeddings.size() << " embeddings for employee " << employee_id << std::endl;
    return embeddings;
}

bool ArcFaceProcessor::save_embedding(const std::vector<float>& embedding, const std::string& file_path) {
    try {
        std::ofstream file(file_path);
        if (!file.is_open()) {
            return false;
        }
        
        for (size_t i = 0; i < embedding.size(); ++i) {
            file << embedding[i];
            if (i < embedding.size() - 1) {
                file << ",";
            }
        }
        file << std::endl;
        file.close();
        
        return true;
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception saving embedding: " << e.what() << std::endl;
        return false;
    }
}

std::vector<float> ArcFaceProcessor::load_embedding(const std::string& file_path) {
    std::vector<float> embedding;
    
    try {
        std::ifstream file(file_path);
        if (!file.is_open()) {
            return embedding;
        }
        
        std::string line;
        if (std::getline(file, line)) {
            std::stringstream ss(line);
            std::string value;
            
            while (std::getline(ss, value, ',')) {
                try {
                    embedding.push_back(std::stof(value));
                } catch (const std::exception& e) {
                    std::cout << "[WARNING] Failed to parse embedding value: " << value << std::endl;
                }
            }
        }
        file.close();
        
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Exception loading embedding: " << e.what() << std::endl;
    }
    
    return embedding;
}
