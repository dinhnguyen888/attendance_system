#pragma once

// OpenCV wrapper to avoid header conflicts
#define CV_IGNORE_DEBUG_BUILD_GUARD
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/videoio.hpp>
#include <opencv2/objdetect.hpp>
#include <opencv2/highgui.hpp>

// Avoid including problematic headers
#ifdef OPENCV2_STITCHING_HPP
#undef OPENCV2_STITCHING_HPP
#endif
