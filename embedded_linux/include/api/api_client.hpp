#pragma once

#include <string>
#include <map>
#include <vector>
#include <curl/curl.h>
#include <nlohmann/json.hpp>

struct ApiResponse {
    bool success;
    std::string message;
    nlohmann::json data;
    int status_code;
};

struct EmployeeInfo {
    int id;
    std::string name;
    std::string employee_code;
    std::string department;
    std::string position;
    std::string email;
    std::string phone;
    bool face_registered;
};

struct AttendanceRecord {
    int id;
    std::string date;
    std::string check_in;
    std::string check_out;
    double total_hours;
    std::string status;
};

class ApiClient {
private:
    std::string base_url;
    std::string auth_token;
    std::string current_employee_id;
    CURL* curl;
    
    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp);
    
public:
    ApiClient(const std::string& server_url);
    ~ApiClient();
    
    // Authentication
    ApiResponse Login(const std::string& employee_code, const std::string& password = "");
    bool IsAuthenticated() const { return !auth_token.empty(); }
    std::string GetCurrentEmployeeId() const { return current_employee_id; }
    
    // Employee operations
    ApiResponse GetEmployeeProfile();
    ApiResponse RegisterEmployeeFace(const std::string& image_path);
    
    // Attendance operations
    ApiResponse CheckIn(const std::string& employee_id, const std::string& image_path);
    ApiResponse CheckOut(const std::string& employee_id, const std::string& image_path);
    ApiResponse GetAttendanceStatus();
    ApiResponse GetAttendanceHistory(const std::string& start_date = "", const std::string& end_date = "");
    ApiResponse GetAttendanceCalendar(int month, int year);
    
private:
    ApiResponse MakeRequest(const std::string& endpoint, const std::string& method = "GET", 
                           const nlohmann::json& data = {}, const std::string& image_path = "");
    void SetHeaders(struct curl_slist** headers);
    std::string EncodeImageToBase64(const std::string& image_path);
};
