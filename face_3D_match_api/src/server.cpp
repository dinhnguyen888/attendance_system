#include "server.h"
#include "video_processing.h"
#include "face_processing.h"
#include "embeddings.h"
#include "files.h"
#include "http_client.h"
#include <sstream>
#include <iomanip>

using json = crow::json::wvalue;

// Base64 encoding function
std::string base64_encode(unsigned char const* bytes_to_encode, unsigned int in_len) {
    std::string ret;
    int i = 0;
    int j = 0;
    unsigned char char_array_3[3];
    unsigned char char_array_4[4];
    
    const std::string chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

    while (in_len--) {
        char_array_3[i++] = *(bytes_to_encode++);
        if (i == 3) {
            char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
            char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
            char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
            char_array_4[3] = char_array_3[2] & 0x3f;

            for(i = 0; (i <4) ; i++)
                ret += chars[char_array_4[i]];
            i = 0;
        }
    }

    if (i) {
        for(j = i; j < 3; j++)
            char_array_3[j] = '\0';

        char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
        char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
        char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
        char_array_4[3] = char_array_3[2] & 0x3f;

        for (j = 0; (j < i + 1); j++)
            ret += chars[char_array_4[j]];

        while((i++ < 3))
            ret += '=';
    }

    return ret;
}

// Function to call Odoo 3D scan API
bool call_odoo_3d_scan_api(const std::string& action, const std::string& employee_id, 
                          const std::vector<uint8_t>& image_data, const std::vector<uint8_t>& comparison_image_data,
                          double confidence, const std::string& message, const std::string& wifi_ip = "UNKNOWN_WIFI") {
    try {
        std::string odoo_url = "http://odoo:8069/3d-scan/" + action;
        std::cout << "[DEBUG] Calling Odoo API: " << odoo_url << std::endl;
        
        // Prepare form data
        std::map<std::string, std::string> form_data;
        form_data["employee_id"] = employee_id;
        form_data["confidence"] = std::to_string(confidence);
        form_data["verification_message"] = message;
        form_data["wifi_ip"] = wifi_ip;
        form_data["csrf_token"] = "false";  // Disable CSRF for this endpoint
        
        // Prepare file data
        std::map<std::string, std::vector<uint8_t>> files;
        std::string file_field_name = (action == "check-in") ? "check_in_image" : "check_out_image";
        files[file_field_name] = image_data;
        
        // Add comparison image if available
        if (!comparison_image_data.empty()) {
            files["comparison_image"] = comparison_image_data;
        }
        
        // Make HTTP request
        HttpResponse response = HttpClient::post(odoo_url, form_data, files);
        
        if (response.success && response.status_code == 200) {
            std::cout << "[INFO] Successfully called Odoo " << action << " API" << std::endl;
            std::cout << "[DEBUG] Response body: " << response.body << std::endl;
            return true;
        } else {
            std::cerr << "[ERROR] Failed to call Odoo " << action << " API. Status: " 
                      << response.status_code << std::endl;
            std::cerr << "[ERROR] Response body: " << response.body << std::endl;
            std::cerr << "[ERROR] Request URL: " << odoo_url << std::endl;
            return false;
        }
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] Exception calling Odoo " << action << " API: " << e.what() << std::endl;
        return false;
    }
}

void register_routes(crow::SimpleApp& app) {
    CROW_ROUTE(app, "/api/health").methods(crow::HTTPMethod::GET)([](const crow::request& req, crow::response& res) {
        json result; result["status"] = "ok";
        res.code = 200;
        res.body = result.dump();
        res.add_header("Content-Type", "application/json");
        res.add_header("Access-Control-Allow-Origin", "*");
        res.end();
    });

    CROW_ROUTE(app, "/api/3d-face-register").methods(crow::HTTPMethod::POST)([](const crow::request& req, crow::response& res) {
        crow::multipart::message body(req);
        auto employeeField = body.get_part_by_name("employee_id");
        auto videoField = body.get_part_by_name("video");

        if (employeeField.body.empty() || videoField.body.empty()) {
            json err; err["message"] = "Missing employee_id or video";
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        std::string employeeId = employeeField.body;
        std::vector<uint8_t> videoBytes(videoField.body.begin(), videoField.body.end());

        // Step 1: Validate
        auto val = validate_video_faces(videoBytes);
        if (!val.ok) {
            json err; err["message"] = val.message;
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        // Step 2: Save video
        auto videoPath = save_video(employeeId, videoBytes);

        // Step 3: Extract frames from saved video file
        auto frames = extract_representative_frames_from_file(videoPath, 10);
        std::cout << "[DEBUG] Extracted " << frames.size() << " frames from video" << std::endl;
        if (frames.size() != 10) {
            json err; 
            err["message"] = "Failed to extract frames. Got " + std::to_string(frames.size()) + " frames, expected 10";
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }
        auto framesDir = save_frames(employeeId, frames);

        // Step 4: Preprocess with enhanced face detection and quality improvement
        auto preprocessed = preprocess_faces(frames);
        auto preDir = save_preprocessed_frames(employeeId, preprocessed);

        // Step 5: Embeddings
        auto embs = compute_embeddings(preprocessed);
        auto embDir = save_embeddings(employeeId, embs);

        // Optional mean vector
        auto mean = compute_mean_embedding(embs);
        save_mean_embedding(employeeId, mean);

        json result;
        result["message"] = "Face registered successfully";
        result["video"] = videoPath;
        result["frames_dir"] = framesDir;
        result["preprocess_dir"] = preDir;
        result["embedding_dir"] = embDir;
        res.code = 200;
        res.body = result.dump();
        res.add_header("Content-Type", "application/json");
        res.add_header("Access-Control-Allow-Origin", "*");
        res.end();
    });

    // Check-in endpoint
    CROW_ROUTE(app, "/api/checkin").methods(crow::HTTPMethod::POST)([](const crow::request& req, crow::response& res) {
        crow::multipart::message body(req);
        auto employeeField = body.get_part_by_name("employee_id");
        auto videoField = body.get_part_by_name("video");

        if (employeeField.body.empty() || videoField.body.empty()) {
            json err; err["message"] = "Missing employee_id or video";
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        std::string employeeId = employeeField.body;
        std::vector<uint8_t> videoBytes(videoField.body.begin(), videoField.body.end());

        // Step 1: Validate video
        auto val = validate_video_faces(videoBytes);
        if (!val.ok) {
            json err; err["message"] = val.message;
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        // Step 2: Extract single best frame
        auto frames = extract_representative_frames(videoBytes, 1);
        if (frames.empty()) {
            json err; err["message"] = "Failed to extract frame from video";
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        // Step 3: Preprocess face
        auto preprocessed = preprocess_faces(frames);
        if (preprocessed.empty()) {
            json err; err["message"] = "Failed to preprocess face";
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        // Step 4: Compute embedding
        auto embs = compute_embeddings(preprocessed);
        if (embs.empty()) {
            json err; err["message"] = "Failed to compute embedding";
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        // Step 5: Compare with stored embeddings
        auto comparison = compare_face_embedding(embs[0], employeeId);
        
        // Step 6: Save comparison image
        std::string comparisonImagePath = save_comparison_image(employeeId, preprocessed[0], "checkin");

        json result;
        result["employee_id"] = employeeId;
        result["similarity"] = comparison.similarity;
        result["match"] = comparison.match;
        result["message"] = comparison.message;
        
        // Convert comparison image to base64
        std::string comparison_image_base64 = "";
        if (!comparisonImagePath.empty()) {
            cv::Mat comparison_img = cv::imread(comparisonImagePath);
            if (!comparison_img.empty()) {
                std::vector<uint8_t> img_buffer;
                cv::imencode(".jpg", comparison_img, img_buffer);
                std::string encoded = base64_encode(img_buffer.data(), img_buffer.size());
                comparison_image_base64 = "data:image/jpeg;base64," + encoded;
            }
        }
        result["comparison_image"] = comparison_image_base64;
        
        // Return 401 for failed verification, 200 for success
        if (comparison.match) {
            res.code = 200;
        } else {
            res.code = 401;
        }
        res.body = result.dump();
        res.add_header("Content-Type", "application/json");
        res.add_header("Access-Control-Allow-Origin", "*");
        res.end();
    });

    // Check-out endpoint
    CROW_ROUTE(app, "/api/checkout").methods(crow::HTTPMethod::POST)([](const crow::request& req, crow::response& res) {
        crow::multipart::message body(req);
        auto employeeField = body.get_part_by_name("employee_id");
        auto videoField = body.get_part_by_name("video");

        if (employeeField.body.empty() || videoField.body.empty()) {
            json err; err["message"] = "Missing employee_id or video";
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        std::string employeeId = employeeField.body;
        std::vector<uint8_t> videoBytes(videoField.body.begin(), videoField.body.end());

        // Step 1: Validate video
        auto val = validate_video_faces(videoBytes);
        if (!val.ok) {
            json err; err["message"] = val.message;
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        // Step 2: Extract single best frame
        auto frames = extract_representative_frames(videoBytes, 1);
        if (frames.empty()) {
            json err; err["message"] = "Failed to extract frame from video";
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        // Step 3: Preprocess face
        auto preprocessed = preprocess_faces(frames);
        if (preprocessed.empty()) {
            json err; err["message"] = "Failed to preprocess face";
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        // Step 4: Compute embedding
        auto embs = compute_embeddings(preprocessed);
        if (embs.empty()) {
            json err; err["message"] = "Failed to compute embedding";
            res.code = 400;
            res.body = err.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
            res.end();
            return;
        }

        // Step 5: Compare with stored embeddings
        auto comparison = compare_face_embedding(embs[0], employeeId);
        
        // Step 6: Save comparison image
        std::string comparisonImagePath = save_comparison_image(employeeId, preprocessed[0], "checkout");

        json result;
        result["employee_id"] = employeeId;
        result["similarity"] = comparison.similarity;
        result["match"] = comparison.match;
        result["message"] = comparison.message;
        
        // Convert comparison image to base64
        std::string comparison_image_base64 = "";
        if (!comparisonImagePath.empty()) {
            cv::Mat comparison_img = cv::imread(comparisonImagePath);
            if (!comparison_img.empty()) {
                std::vector<uint8_t> img_buffer;
                cv::imencode(".jpg", comparison_img, img_buffer);
                std::string encoded = base64_encode(img_buffer.data(), img_buffer.size());
                comparison_image_base64 = "data:image/jpeg;base64," + encoded;
            }
        }
        result["comparison_image"] = comparison_image_base64;
        
        // Return 401 for failed verification, 200 for success
        if (comparison.match) {
            res.code = 200;
        } else {
            res.code = 401;
        }
        res.body = result.dump();
        res.add_header("Content-Type", "application/json");
        res.add_header("Access-Control-Allow-Origin", "*");
        res.end();
    });

    // File browser endpoint for accessing training data
    CROW_ROUTE(app, "/api/access-train-data").methods(crow::HTTPMethod::GET)([](const crow::request& req, crow::response& res) {
        try {
            // Start filebrowser on port 8081 pointing to employee data directory
            std::string command = "filebrowser -a 0.0.0.0 -p 8081 -r /app/employee_data --noauth > /dev/null 2>&1 &";
            int result = system(command.c_str());
            
            if (result == 0) {
                // Redirect to filebrowser interface
                res.code = 302;
                res.add_header("Location", "http://localhost:8081");
                res.add_header("Access-Control-Allow-Origin", "*");
                res.body = "Redirecting to file browser...";
            } else {
                json error;
                error["error"] = "Failed to start file browser";
                res.code = 500;
                res.body = error.dump();
                res.add_header("Content-Type", "application/json");
                res.add_header("Access-Control-Allow-Origin", "*");
            }
        } catch (const std::exception& e) {
            json error;
            error["error"] = "Exception starting file browser: " + std::string(e.what());
            res.code = 500;
            res.body = error.dump();
            res.add_header("Content-Type", "application/json");
            res.add_header("Access-Control-Allow-Origin", "*");
        }
        res.end();
    });
}


