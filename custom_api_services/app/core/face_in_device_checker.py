import logging
from typing import Dict, List
import numpy as np
import cv2


logger = logging.getLogger(__name__)


class FaceInDeviceChecker:
    """Kiểm tra mặt người có xuất hiện trong màn hình thiết bị hay không."""

    def __init__(self):
        try:
            from insightface.app import FaceAnalysis
            self.face_detector = FaceAnalysis()
            self.face_detector.prepare(ctx_id=0, det_size=(640, 640))
        except Exception as e:
            logger.error(f"Failed to init InsightFace: {e}")
            self.face_detector = None

    def _crop_device_region(self, image: np.ndarray, device_bbox: List[int]) -> np.ndarray:
        try:
            x1, y1, x2, y2 = device_bbox
            h, w = image.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            return image[y1:y2, x1:x2]
        except Exception:
            return image

    def _is_active_screen(self, device_region: np.ndarray) -> bool:
        try:
            if device_region.size == 0:
                return False
            gray = cv2.cvtColor(device_region, cv2.COLOR_BGR2GRAY) if len(device_region.shape) == 3 else device_region
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            has_variation = std_brightness > 15
            is_bright_enough = mean_brightness > 30
            has_edges = edge_density > 0.01
            return (has_variation and is_bright_enough) or has_edges
        except Exception:
            return True

    def check_face_in_device(self, image: np.ndarray, device_bbox: List[int]) -> Dict:
        if self.face_detector is None:
            return {'face_in_device': False, 'error': 'Face detector not available'}
        try:
            device_region = self._crop_device_region(image, device_bbox)
            is_active_screen = self._is_active_screen(device_region)
            if not is_active_screen:
                return {'face_in_device': False, 'reason': 'Device screen appears inactive/black', 'screen_active': False, 'face_count': 0}
            faces = self.face_detector.get(device_region)
            if len(faces) == 0:
                return {'face_in_device': False, 'reason': 'No face detected in device screen area', 'face_count': 0, 'screen_active': True}
            face_bboxes = []
            for face in faces:
                x1, y1, x2, y2 = face.bbox.astype(int)
                face_bboxes.append((x1, y1, x2 - x1, y2 - y1))
            largest_face = max(face_bboxes, key=lambda f: f[2] * f[3])
            face_x, face_y, face_w, face_h = largest_face
            dx1, dy1, dx2, dy2 = device_bbox
            full_face_bbox = [dx1 + face_x, dy1 + face_y, dx1 + face_x + face_w, dy1 + face_y + face_h]
            device_area = max(1, (dx2 - dx1) * (dy2 - dy1))
            face_area = face_w * face_h
            face_to_device_ratio = face_area / device_area
            is_significant_face = face_to_device_ratio > 0.02
            all_faces = self.face_detector.get(image)
            external_faces = []
            for face in all_faces:
                x1, y1, x2, y2 = face.bbox.astype(int)
                if not (x1 >= dx1 and y1 >= dy1 and x2 <= dx2 and y2 <= dy2):
                    external_faces.append((x2 - x1) * (y2 - y1))
            device_face_area = face_area
            size_spoofing_detected = False
            size_ratio = 1.0
            if external_faces:
                largest_external_face_area = max(external_faces)
                size_ratio = device_face_area / largest_external_face_area
                size_spoofing_detected = size_ratio < 0.8
            face_in_device = is_significant_face and is_active_screen and not size_spoofing_detected
            return {
                'face_in_device': face_in_device,
                'face_bbox': full_face_bbox,
                'device_bbox': device_bbox,
                'face_to_device_ratio': face_to_device_ratio,
                'face_count': len(faces),
                'size_spoofing_detected': size_spoofing_detected,
                'size_ratio': size_ratio,
                'screen_active': is_active_screen,
                'face_area': face_area,
                'is_significant_face': is_significant_face
            }
        except Exception as e:
            logger.error(f"Error in face-in-device detection: {e}")
            return {'face_in_device': False, 'error': str(e)}


