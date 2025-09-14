#include "server.h"
#include "video_processing.h"
#include "face_processing.h"
#include "embeddings.h"
#include "files.h"

using json = crow::json::wvalue;

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
}


