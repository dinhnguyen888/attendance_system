#include "http_client.h"
#include <curl/curl.h>
#include <sstream>
#include <iostream>
#include <iomanip>
#include <cstdint>
#include <ctime>

// Callback function to write response data
static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
    userp->append((char*)contents, size * nmemb);
    return size * nmemb;
}

// Callback function to write response headers
static size_t HeaderCallback(char* buffer, size_t size, size_t nitems, std::map<std::string, std::string>* headers) {
    std::string header(buffer, size * nitems);
    size_t pos = header.find(':');
    if (pos != std::string::npos) {
        std::string key = header.substr(0, pos);
        std::string value = header.substr(pos + 1);
        // Remove leading/trailing whitespace
        key.erase(0, key.find_first_not_of(" \t\r\n"));
        key.erase(key.find_last_not_of(" \t\r\n") + 1);
        value.erase(0, value.find_first_not_of(" \t\r\n"));
        value.erase(value.find_last_not_of(" \t\r\n") + 1);
        (*headers)[key] = value;
    }
    return size * nitems;
}

std::string HttpClient::url_encode(const std::string& value) {
    std::ostringstream escaped;
    escaped.fill('0');
    escaped << std::hex;

    for (char c : value) {
        if (std::isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
            escaped << c;
        } else {
            escaped << std::uppercase;
            escaped << '%' << std::setw(2) << int((unsigned char)c);
            escaped << std::nouppercase;
        }
    }
    return escaped.str();
}

std::string HttpClient::create_multipart_boundary() {
    return "----WebKitFormBoundary" + std::to_string(std::time(nullptr));
}

std::string HttpClient::create_multipart_body(const std::map<std::string, std::string>& form_data,
                                            const std::map<std::string, std::vector<uint8_t>>& files,
                                            const std::string& boundary) {
    std::ostringstream body;
    
    // Add form data fields
    for (const auto& pair : form_data) {
        body << "--" << boundary << "\r\n";
        body << "Content-Disposition: form-data; name=\"" << pair.first << "\"\r\n";
        body << "\r\n";
        body << pair.second << "\r\n";
    }
    
    // Add file fields
    for (const auto& pair : files) {
        body << "--" << boundary << "\r\n";
        body << "Content-Disposition: form-data; name=\"" << pair.first << "\"; filename=\"image.jpg\"\r\n";
        body << "Content-Type: image/jpeg\r\n";
        body << "\r\n";
        body.write(reinterpret_cast<const char*>(pair.second.data()), pair.second.size());
        body << "\r\n";
    }
    
    body << "--" << boundary << "--\r\n";
    return body.str();
}

HttpResponse HttpClient::post(const std::string& url, 
                            const std::map<std::string, std::string>& form_data,
                            const std::map<std::string, std::vector<uint8_t>>& files) {
    HttpResponse response;
    response.success = false;
    
    CURL* curl;
    CURLcode res;
    std::string response_body;
    std::map<std::string, std::string> response_headers;
    
    curl = curl_easy_init();
    if (curl) {
        // Set URL
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        
        // Set POST method
        curl_easy_setopt(curl, CURLOPT_POST, 1L);
        
        // Create multipart body
        std::string boundary = create_multipart_boundary();
        std::string body = create_multipart_body(form_data, files, boundary);
        
        // Set POST data
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, body.length());
        
        // Set headers
        struct curl_slist* headers = nullptr;
        std::string content_type = "multipart/form-data; boundary=" + boundary;
        headers = curl_slist_append(headers, ("Content-Type: " + content_type).c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        
        // Set response callback
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_body);
        
        // Set header callback
        curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION, HeaderCallback);
        curl_easy_setopt(curl, CURLOPT_HEADERDATA, &response_headers);
        
        // Set timeout
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
        
        // Perform request
        res = curl_easy_perform(curl);
        
        if (res == CURLE_OK) {
            long status_code;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &status_code);
            response.status_code = static_cast<int>(status_code);
            response.body = response_body;
            response.headers = response_headers;
            response.success = true;
        } else {
            std::cerr << "[ERROR] HTTP POST failed: " << curl_easy_strerror(res) << std::endl;
            response.status_code = 0;
            response.body = "HTTP request failed: " + std::string(curl_easy_strerror(res));
        }
        
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }
    
    return response;
}

HttpResponse HttpClient::get(const std::string& url) {
    HttpResponse response;
    response.success = false;
    
    CURL* curl;
    CURLcode res;
    std::string response_body;
    std::map<std::string, std::string> response_headers;
    
    curl = curl_easy_init();
    if (curl) {
        // Set URL
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        
        // Set response callback
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_body);
        
        // Set header callback
        curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION, HeaderCallback);
        curl_easy_setopt(curl, CURLOPT_HEADERDATA, &response_headers);
        
        // Set timeout
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
        
        // Perform request
        res = curl_easy_perform(curl);
        
        if (res == CURLE_OK) {
            long status_code;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &status_code);
            response.status_code = static_cast<int>(status_code);
            response.body = response_body;
            response.headers = response_headers;
            response.success = true;
        } else {
            std::cerr << "[ERROR] HTTP GET failed: " << curl_easy_strerror(res) << std::endl;
            response.status_code = 0;
            response.body = "HTTP request failed: " + std::string(curl_easy_strerror(res));
        }
        
        curl_easy_cleanup(curl);
    }
    
    return response;
}
