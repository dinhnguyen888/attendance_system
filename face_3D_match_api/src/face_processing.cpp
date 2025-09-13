#include "face_processing.h"

static cv::Mat skin_normalize(const cv::Mat& img) {
    cv::Mat ycrcb; cv::cvtColor(img, ycrcb, cv::COLOR_BGR2YCrCb);
    std::vector<cv::Mat> ch; cv::split(ycrcb, ch);
    cv::equalizeHist(ch[0], ch[0]);
    cv::merge(ch, ycrcb);
    cv::Mat out; cv::cvtColor(ycrcb, out, cv::COLOR_YCrCb2BGR);
    return out;
}

std::vector<cv::Mat> preprocess_faces(const std::vector<cv::Mat>& frames) {
    std::vector<cv::Mat> out;
    out.reserve(frames.size());
    for (const auto& f : frames) {
        if (f.empty()) continue;
        cv::Mat resized; cv::resize(f, resized, cv::Size(112, 112));
        cv::Mat normed = skin_normalize(resized);
        out.push_back(normed);
    }
    return out;
}


