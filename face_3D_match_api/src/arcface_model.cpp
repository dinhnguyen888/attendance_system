#include "arcface_model.h"
#include <iostream>
#include <cmath>
#include <algorithm>

ArcFaceModel::ArcFaceModel() : initialized_(false) {}

ArcFaceModel::~ArcFaceModel() {}

bool ArcFaceModel::initialize(const std::string& model_path) {
    try {
#ifdef USE_ONNX_RUNTIME
        // Initialize ONNX Runtime
        env_ = std::make_unique<Ort::Env>(ORT_LOGGING_LEVEL_WARNING, "ArcFace");
        session_options_ = std::make_unique<Ort::SessionOptions>();
        session_options_->SetIntraOpNumThreads(1);
        session_options_->SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_EXTENDED);
        
        session_ = std::make_unique<Ort::Session>(*env_, model_path.c_str(), *session_options_);
        
        // Get input/output info (ORT 1.16+ API)
        Ort::AllocatorWithDefaultOptions allocator;
        size_t num_input_nodes = session_->GetInputCount();
        size_t num_output_nodes = session_->GetOutputCount();

        input_names_.clear();
        output_names_.clear();
        input_names_.reserve(num_input_nodes);
        output_names_.reserve(num_output_nodes);

        for (size_t i = 0; i < num_input_nodes; i++) {
            Ort::AllocatedStringPtr name_ptr = session_->GetInputNameAllocated(i, allocator);
            input_name_storage_.emplace_back(name_ptr.get());
            input_names_.push_back(input_name_storage_.back().c_str());

            Ort::TypeInfo input_type_info = session_->GetInputTypeInfo(i);
            auto input_tensor_info = input_type_info.GetTensorTypeAndShapeInfo();
            input_shape_ = input_tensor_info.GetShape();
        }

        for (size_t i = 0; i < num_output_nodes; i++) {
            Ort::AllocatedStringPtr name_ptr = session_->GetOutputNameAllocated(i, allocator);
            output_name_storage_.emplace_back(name_ptr.get());
            output_names_.push_back(output_name_storage_.back().c_str());
        }
        
        std::cout << "ONNX Runtime ArcFace (ResNet100) model loaded successfully" << std::endl;
#else
        // Use OpenCV DNN as fallback
        net_ = cv::dnn::readNetFromONNX(model_path);
        if (net_.empty()) {
            std::cerr << "Failed to load ArcFace model with OpenCV DNN: " << model_path << std::endl;
            return false;
        }
        std::cout << "OpenCV DNN ArcFace (ResNet100) model loaded successfully" << std::endl;
#endif
        
        initialized_ = true;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "ArcFace model initialization error: " << e.what() << std::endl;
        return false;
    }
}

std::vector<float> ArcFaceModel::extractEmbedding(const cv::Mat& face_image) {
    std::vector<float> embedding;
    
    if (!initialized_ || face_image.empty()) {
        return embedding;
    }
    
    try {
        cv::Mat preprocessed = preprocessForArcFace(face_image);
        
#ifdef USE_ONNX_RUNTIME
        // ONNX Runtime inference
        std::vector<int64_t> input_shape = {1, 3, 112, 112};
        size_t input_tensor_size = 1 * 3 * 112 * 112;
        std::vector<float> input_tensor_values(input_tensor_size);
        
        // Convert Mat to tensor format (CHW)
        std::vector<cv::Mat> channels(3);
        cv::split(preprocessed, channels);
        
        for (int c = 0; c < 3; ++c) {
            std::memcpy(input_tensor_values.data() + c * 112 * 112, 
                       channels[c].ptr<float>(), 112 * 112 * sizeof(float));
        }
        
        // Create input tensor
        Ort::MemoryInfo memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
        Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
            memory_info, input_tensor_values.data(), input_tensor_size, 
            input_shape.data(), input_shape.size());
        
        // Run inference
        auto output_tensors = session_->Run(Ort::RunOptions{nullptr}, 
                                          input_names_.data(), &input_tensor, 1, 
                                          output_names_.data(), 1);
        
        // Extract embedding
        float* output_data = output_tensors.front().GetTensorMutableData<float>();
        auto output_shape = output_tensors.front().GetTensorTypeAndShapeInfo().GetShape();
        size_t output_size = output_shape[1]; // Usually 512 for ArcFace
        
        embedding.assign(output_data, output_data + output_size);
#else
        // OpenCV DNN inference
        cv::Mat blob = cv::dnn::blobFromImage(preprocessed, 1.0, cv::Size(112, 112), cv::Scalar(0, 0, 0), true, false);
        net_.setInput(blob);
        cv::Mat output = net_.forward();
        
        // Extract embedding
        embedding.assign(output.ptr<float>(), output.ptr<float>() + output.total());
#endif
        
        // Normalize embedding
        embedding = normalizeEmbedding(embedding);
        
    } catch (const std::exception& e) {
        std::cerr << "Embedding extraction error: " << e.what() << std::endl;
    }
    
    return embedding;
}

float ArcFaceModel::calculateSimilarity(const std::vector<float>& embedding1, const std::vector<float>& embedding2) {
    if (embedding1.size() != embedding2.size() || embedding1.empty()) {
        return 0.0f;
    }
    
    // Cosine similarity
    float dot_product = 0.0f;
    float norm1 = 0.0f;
    float norm2 = 0.0f;
    
    for (size_t i = 0; i < embedding1.size(); ++i) {
        dot_product += embedding1[i] * embedding2[i];
        norm1 += embedding1[i] * embedding1[i];
        norm2 += embedding2[i] * embedding2[i];
    }
    
    if (norm1 == 0.0f || norm2 == 0.0f) {
        return 0.0f;
    }
    
    return dot_product / (std::sqrt(norm1) * std::sqrt(norm2));
}

cv::Mat ArcFaceModel::preprocessForArcFace(const cv::Mat& face) {
    cv::Mat processed;
    
    // Resize to 112x112 if not already
    if (face.size() != cv::Size(112, 112)) {
        cv::resize(face, processed, cv::Size(112, 112));
    } else {
        processed = face.clone();
    }
    
    // Convert to float and normalize to [-1, 1]
    processed.convertTo(processed, CV_32F);
    processed = (processed - 127.5) / 127.5;
    
    return processed;
}

std::vector<float> ArcFaceModel::normalizeEmbedding(const std::vector<float>& embedding) {
    std::vector<float> normalized = embedding;
    
    // L2 normalization
    float norm = 0.0f;
    for (float val : embedding) {
        norm += val * val;
    }
    norm = std::sqrt(norm);
    
    if (norm > 0.0f) {
        for (float& val : normalized) {
            val /= norm;
        }
    }
    
    return normalized;
}
