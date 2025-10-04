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
EMPLOYEE_EMBEDDINGS_DIR = "employee_embeddings"

# Face recognition thresholds (optimized based on actual performance)
ARCFACE_THRESHOLD = 0.5   # Primary ArcFace embedding threshold (realistic for same person)
LBP_ORB_THRESHOLD = 0.45  # Backup LBP+ORB threshold (lower due to method limitations)
CANNY_THRESHOLD = 0.15    # Backup Canny threshold (lower for edge features)
COSINE_THRESHOLD = 0.5    # Legacy compatibility (same as ARCFACE_THRESHOLD)
MAX_EMBEDDINGS_PER_EMPLOYEE = 8  # Increased for augmented enrollment

# Confidence thresholds for method selection (adjusted for realistic performance)
HIGH_CONFIDENCE_THRESHOLD = 0.7  # Use ArcFace only if above this
LOW_CONFIDENCE_THRESHOLD = 0.35  # Use backup methods if below this

# Augmentation settings
NUM_AUGMENTATIONS = 8     # Number of augmented variations to generate
MIN_QUALITY_SCORE = 0.4   # Minimum quality score for enrollment

# Image validation settings
ASPECT_RATIO_3_4 = 3.0 / 4.0
ASPECT_RATIO_4_6 = 4.0 / 6.0
ASPECT_RATIO_TOLERANCE = 0.05



# HSV-based background validation (only white/blue allowed)
# OpenCV HSV ranges: H [0,179], S [0,255], V [0,255]
WHITE_S_MAX = 30   # low saturation for white
WHITE_V_MIN = 200  # high brightness for white

BLUE_H_MIN = 100   # blue hue lower bound
BLUE_H_MAX = 130   # blue hue upper bound
BLUE_S_MIN = 60    # minimum saturation for blue
BLUE_V_MIN = 60    # minimum brightness for blue

# At least this ratio of border pixels must match white or blue to accept
BG_RATIO_THRESHOLD = 0.7

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
