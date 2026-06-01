"""Device-presentation spoofing checks."""
import logging
import os

import cv2
import numpy as np

from app.inference.models import get_yolo_detector
from app.inference.yolo_detector import YOLOv11DeviceDetector

DEVICE_CONFIDENCE_THRESHOLD = float(os.getenv("DEVICE_CONFIDENCE_THRESHOLD", "0.15"))
DEVICE_DOMINANT_AREA_THRESHOLD = float(os.getenv("DEVICE_DOMINANT_AREA_THRESHOLD", "0.25"))
FACE_IN_DEVICE_AREA_RATIO = float(os.getenv("FACE_IN_DEVICE_AREA_RATIO", "0.02"))
INSIGHTFACE_DET_SIZE = int(os.getenv("INSIGHTFACE_DET_SIZE", "640"))
_logger = logging.getLogger(__name__)


class AntiSpoofingVerifier:
    def __init__(self):
        self.device_detector = get_yolo_detector() or YOLOv11DeviceDetector()
        self.face_checker = FaceInDeviceChecker()

    def verify_no_device_spoofing(self, image: np.ndarray):
        try:
            if not self.device_detector.model_loaded:
                self.device_detector._load_model_with_progress()
                if not self.device_detector.model_loaded:
                    return {"spoofing_detected": False, "reason": "MODEL_UNAVAILABLE", "verification_passed": True}

            devices = self.device_detector.detect_devices(image, confidence_threshold=DEVICE_CONFIDENCE_THRESHOLD)
            if not devices:
                return {"spoofing_detected": False, "reason": "NO_DEVICE", "verification_passed": True}

            for device in devices:
                bbox = device["bbox"]
                if self.device_detector.is_device_dominant(bbox, image.shape[:2], area_threshold=DEVICE_DOMINANT_AREA_THRESHOLD):
                    return self._spoofed(device, "DEVICE_DOMINANT")
                if self.face_checker.check_face_in_device(image, bbox).get("face_in_device", False):
                    return self._spoofed(device, "FACE_IN_DEVICE")

            return {"spoofing_detected": False, "reason": "NO_SPOOFING", "verification_passed": True}
        except Exception as exc:
            _logger.error("SPOOFING_CHECK_FAILED: %s", exc)
            return {"spoofing_detected": False, "reason": "ERROR", "verification_passed": True}

    @staticmethod
    def _spoofed(device, reason):
        return {
            "spoofing_detected": True,
            "spoofing_type": "device_presentation_attack",
            "spoofing_device": device["class_name"],
            "device_confidence": device["confidence"],
            "reason": reason,
            "verification_passed": False,
        }


class FaceInDeviceChecker:
    def __init__(self):
        try:
            from insightface.app import FaceAnalysis
            self.face_detector = FaceAnalysis()
            self.face_detector.prepare(ctx_id=0, det_size=(INSIGHTFACE_DET_SIZE, INSIGHTFACE_DET_SIZE))
        except Exception as exc:
            _logger.error("FACE_IN_DEVICE_INIT_FAILED: %s", exc)
            self.face_detector = None

    def check_face_in_device(self, image: np.ndarray, device_bbox):
        if self.face_detector is None:
            return {"face_in_device": False, "reason": "MODEL_UNAVAILABLE"}
        try:
            region = self._crop(image, device_bbox)
            if not self._active_screen(region):
                return {"face_in_device": False, "reason": "SCREEN_INACTIVE"}
            faces = self.face_detector.get(region)
            if not faces:
                return {"face_in_device": False, "reason": "NO_FACE_IN_DEVICE"}

            face = max(faces, key=lambda item: (item.bbox[2] - item.bbox[0]) * (item.bbox[3] - item.bbox[1]))
            x1, y1, x2, y2 = face.bbox.astype(int)
            device_area = max(1, (device_bbox[2] - device_bbox[0]) * (device_bbox[3] - device_bbox[1]))
            face_area = max(0, (x2 - x1) * (y2 - y1))
            return {"face_in_device": face_area / device_area > FACE_IN_DEVICE_AREA_RATIO}
        except Exception as exc:
            _logger.error("FACE_IN_DEVICE_CHECK_FAILED: %s", exc)
            return {"face_in_device": False, "reason": "ERROR"}

    @staticmethod
    def _crop(image: np.ndarray, bbox):
        x1, y1, x2, y2 = bbox
        h, w = image.shape[:2]
        return image[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

    @staticmethod
    def _active_screen(region: np.ndarray) -> bool:
        if region.size == 0:
            return False
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if len(region.shape) == 3 else region
        edges = cv2.Canny(gray, 50, 150)
        return (np.std(gray) > 15 and np.mean(gray) > 30) or (np.sum(edges > 0) / edges.size > 0.01)
