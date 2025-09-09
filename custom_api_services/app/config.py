"""
Configuration settings for Face Recognition API
"""
import os

# API Configuration
API_TITLE = "Face Recognition API"
API_VERSION = "2.0.0"

# Directory paths
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

# Image processing
TARGET_SIZE = (640, 640)
STANDARD_FACE_SIZE = (112, 112)
TARGET_WIDTH = 480

# InsightFace configuration
os.environ["INSIGHTFACE_USE_TORCH"] = "0"
os.environ["ONNXRUNTIME_FORCE_CPU"] = "1"

# Create directories if they don't exist
for directory in [EMPLOYEE_FACES_DIR, EMPLOYEE_CANNY_FEATURES_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
