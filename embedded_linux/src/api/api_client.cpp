#include "api/api_client.hpp"
#include "config/config_manager.hpp"
#include <curl/curl.h>
#include <nlohmann/json.hpp>
#include <fstream>
#include <sstream>
#include <iostream>
#include <cstring>

ApiClient::ApiClient(const std::string& server_url) : base_url(server_url) {
    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();
}

ApiClient::~ApiClient() {
    if (curl) {
        curl_easy_cleanup(curl);
    }
    curl_global_cleanup();
}

size_t ApiClient::WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
    size_t totalSize = size * nmemb;
    userp->append((char*)contents, totalSize);
    return totalSize;
}

ApiResponse ApiClient::Login(const std::string& employee_code, const std::string& /* password */) {
    // For embedded system, only use employee code - no password required
    nlohmann::json login_data = {
        {"employee_code", employee_code},
        {"auth_mode", "employee_only"}
    };
    
    ApiResponse response = MakeRequest("/embedded/auth/login", "POST", login_data);
    
    if (response.success) {
        // Store employee info for embedded device
        auth_token = "embedded_authenticated";
        if (response.data.contains("employee_id")) {
            current_employee_id = std::to_string(response.data["employee_id"].get<int>());
        }
    }
    
    return response;
}

ApiResponse ApiClient::GetEmployeeProfile() {
    return MakeRequest("/mobile/employee/profile", "GET");
}

ApiResponse ApiClient::RegisterEmployeeFace(const std::string& image_path) {
    return MakeRequest("/mobile/employee/register-face", "POST", {}, image_path);
}

ApiResponse ApiClient::CheckIn(const std::string& employee_id, const std::string& image_path) {
    nlohmann::json data;
    data["employee_id"] = employee_id;
    data["wifi_ip"] = "192.168.1.100"; // This could be made configurable
    return MakeRequest("/embedded/attendance/check-in", "POST", data, image_path);
}

ApiResponse ApiClient::CheckOut(const std::string& employee_id, const std::string& image_path) {
    nlohmann::json data;
    data["employee_id"] = employee_id;
    data["wifi_ip"] = "192.168.1.100"; // This could be made configurable
    return MakeRequest("/embedded/attendance/check-out", "POST", data, image_path);
}

ApiResponse ApiClient::GetAttendanceStatus() {
    return MakeRequest("/mobile/attendance/status", "GET");
}

ApiResponse ApiClient::GetAttendanceHistory(const std::string& start_date, const std::string& end_date) {
    std::string endpoint = "/mobile/attendance/history";
    if (!start_date.empty() || !end_date.empty()) {
        endpoint += "?";
        if (!start_date.empty()) {
            endpoint += "start_date=" + start_date;
        }
        if (!end_date.empty()) {
            if (!start_date.empty()) endpoint += "&";
            endpoint += "end_date=" + end_date;
        }
    }
    return MakeRequest(endpoint, "GET");
}

ApiResponse ApiClient::GetAttendanceCalendar(int month, int year) {
    std::string endpoint = "/mobile/attendance/calendar?month=" + std::to_string(month) + "&year=" + std::to_string(year);
    return MakeRequest(endpoint, "GET");
}

ApiResponse ApiClient::MakeRequest(const std::string& endpoint, const std::string& method, 
                                  const nlohmann::json& data, const std::string& image_path) {
    ApiResponse response;
    response.success = false;
    response.status_code = 0;
    
    if (!curl) {
        response.message = "CURL not initialized";
        return response;
    }
    
    std::string url = base_url + endpoint;
    std::string response_string;
    
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_string);
    
    struct curl_slist* headers = nullptr;
    SetHeaders(&headers);
    
    std::string post_data;
    
    if (method == "POST") {
        curl_easy_setopt(curl, CURLOPT_POST, 1L);
        
        if (!image_path.empty()) {
            // Multipart form data for image upload
            curl_mime* mime = curl_mime_init(curl);
            curl_mimepart* part;
            
            // Add individual data fields for embedded endpoints
            if (!data.empty()) {
                for (auto& [key, value] : data.items()) {
                    part = curl_mime_addpart(mime);
                    curl_mime_name(part, key.c_str());
                    std::string value_str = value.is_string() ? value.get<std::string>() : value.dump();
                    curl_mime_data(part, value_str.c_str(), CURL_ZERO_TERMINATED);
                }
            }
            
            // Add image file part
            part = curl_mime_addpart(mime);
            curl_mime_name(part, "image");
            curl_mime_filedata(part, image_path.c_str());
            curl_mime_type(part, "image/jpeg");
            
            curl_easy_setopt(curl, CURLOPT_MIMEPOST, mime);
        } else if (!data.empty()) {
            post_data = data.dump();
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_data.c_str());
            curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, post_data.length());
        }
    }
    
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    
    CURLcode res = curl_easy_perform(curl);
    
    if (res == CURLE_OK) {
        long response_code;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
        response.status_code = static_cast<int>(response_code);
        
        try {
            nlohmann::json json_response = nlohmann::json::parse(response_string);
            
            if (json_response.contains("success")) {
                response.success = json_response["success"];
            } else {
                response.success = (response_code >= 200 && response_code < 300);
            }
            
            if (json_response.contains("message")) {
                response.message = json_response["message"];
            }
            
            response.data = json_response;
            
        } catch (const std::exception& e) {
            response.success = false;
            response.message = "Invalid JSON response: " + std::string(e.what());
        }
    } else {
        response.message = "Request failed: " + std::string(curl_easy_strerror(res));
    }
    
    if (headers) {
        curl_slist_free_all(headers);
    }
    
    return response;
}

void ApiClient::SetHeaders(struct curl_slist** headers) {
    *headers = curl_slist_append(*headers, "Content-Type: application/json");
    
    if (!auth_token.empty()) {
        std::string auth_header = "Authorization: Bearer " + auth_token;
        *headers = curl_slist_append(*headers, auth_header.c_str());
    }
}

std::string ApiClient::EncodeImageToBase64(const std::string& image_path) {
    std::ifstream file(image_path, std::ios::binary);
    if (!file) {
        return "";
    }
    
    std::ostringstream buffer;
    buffer << file.rdbuf();
    std::string image_data = buffer.str();
    
    // Base64 encoding implementation
    const std::string chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string encoded;
    int val = 0, valb = -6;
    
    for (unsigned char c : image_data) {
        val = (val << 8) + c;
        valb += 8;
        while (valb >= 0) {
            encoded.push_back(chars[(val >> valb) & 0x3F]);
            valb -= 6;
        }
    }
    
    if (valb > -6) {
        encoded.push_back(chars[((val << 8) >> (valb + 8)) & 0x3F]);
    }
    
    while (encoded.size() % 4) {
        encoded.push_back('=');
    }
    
    return encoded;
}
