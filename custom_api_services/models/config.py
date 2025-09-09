"""
Configuration constants and settings for face recognition API
"""
import os

# Directory configurations
EMPLOYEE_FACES_DIR = "employee_faces"
EMPLOYEE_CANNY_FEATURES_DIR = "employee_canny_features"

# Face recognition thresholds
COSINE_THRESHOLD = 0.7
CANNY_THRESHOLD = 0.2
MAX_EMBEDDINGS_PER_EMPLOYEE = 5

# Image validation settings
ASPECT_RATIO_3_4 = 3.0 / 4.0
ASPECT_RATIO_4_6 = 4.0 / 6.0
ASPECT_RATIO_TOLERANCE = 0.05

# Background color validation
WHITE_THRESHOLD = 50
BLUE_THRESHOLD = 150

# Face detection parameters
MIN_FACE_SIZE = (80, 80)
SCALE_FACTOR = 1.05
MIN_NEIGHBORS = 6

# Image processing parameters
TARGET_IMAGE_WIDTH = 480
STANDARD_FACE_SIZE = (112, 112)
DETECTION_SIZE = (640, 640)

# Skin tone normalization
OPTIMAL_SKIN_COLOR_BGR = [180, 160, 140]
TARGET_BRIGHTNESS = 160

# Environment variables
os.environ["INSIGHTFACE_USE_TORCH"] = "0"
os.environ["ONNXRUNTIME_FORCE_CPU"] = "1"

# Create directories if they don't exist
if not os.path.exists(EMPLOYEE_FACES_DIR):
    os.makedirs(EMPLOYEE_FACES_DIR)

if not os.path.exists(EMPLOYEE_CANNY_FEATURES_DIR):
    os.makedirs(EMPLOYEE_CANNY_FEATURES_DIR)
