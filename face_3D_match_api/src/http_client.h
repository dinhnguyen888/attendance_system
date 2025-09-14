#pragma once
#include <string>
#include <vector>
#include <map>
#include <cstdint>

struct HttpResponse {
    int status_code;
    std::string body;
    std::map<std::string, std::string> headers;
    bool success;
};

class HttpClient {
public:
    static HttpResponse post(const std::string& url, 
                           const std::map<std::string, std::string>& form_data,
                           const std::map<std::string, std::vector<uint8_t>>& files);
    
    static HttpResponse get(const std::string& url);
    
private:
    static std::string url_encode(const std::string& value);
    static std::string create_multipart_boundary();
    static std::string create_multipart_body(const std::map<std::string, std::string>& form_data,
                                           const std::map<std::string, std::vector<uint8_t>>& files,
                                           const std::string& boundary);
};
