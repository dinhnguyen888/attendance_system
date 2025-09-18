import logging
from typing import Dict
import numpy as np

from app.core.yolo_detector import YOLOv11DeviceDetector
from app.core.face_in_device_checker import FaceInDeviceChecker
from app.models.face_models import get_yolo_detector


logger = logging.getLogger(__name__)


class AntiSpoofingVerifier:
    """Verifier dùng detector + checker để phát hiện gian lận qua thiết bị."""

    def __init__(self):
        # Dùng singleton để giảm chi phí load model
        self.device_detector = get_yolo_detector() or YOLOv11DeviceDetector()
        self.face_checker = FaceInDeviceChecker()

    def verify_no_device_spoofing(self, image: np.ndarray) -> Dict:
        try:
            if not self.device_detector.model_loaded:
                self.device_detector._load_model_with_progress()
                if not self.device_detector.model_loaded:
                    return {
                        'spoofing_detected': False,
                        'reason': 'YOLO model unavailable - verification skipped',
                        'verification_passed': True,
                        'model_error': True
                    }

            devices = self.device_detector.detect_devices(image, confidence_threshold=0.15)
            if not devices:
                return {
                    'spoofing_detected': False,
                    'reason': 'No devices detected in frame',
                    'devices_found': 0,
                    'verification_passed': True
                }

            for device in devices:
                device_name = device['class_name']
                device_bbox = device['bbox']
                device_confidence = device['confidence']

                if self.device_detector.is_device_dominant(device_bbox, image.shape[:2], area_threshold=0.25):
                    return {
                        'spoofing_detected': True,
                        'spoofing_type': 'device_presentation_attack',
                        'spoofing_device': device_name,
                        'device_confidence': device_confidence,
                        'reason': 'Vui lòng không đưa điện thoại/laptop vào sát khung hình khi xác thực',
                        'verification_passed': False,
                        'devices_found': len(devices)
                    }

                face_check = self.face_checker.check_face_in_device(image, device_bbox)
                if face_check.get('face_in_device', False):
                    return {
                        'spoofing_detected': True,
                        'spoofing_type': 'device_presentation_attack',
                        'spoofing_device': device_name,
                        'device_confidence': device_confidence,
                        'face_overlap_ratio': face_check.get('overlap_ratio', 0),
                        'face_to_device_ratio': face_check.get('face_to_device_ratio', 0),
                        'reason': 'Khuôn mặt xuất hiện trong màn hình thiết bị',
                        'verification_passed': False,
                        'devices_found': len(devices)
                    }

            return {
                'spoofing_detected': False,
                'reason': 'Devices present but no spoofing indicators',
                'devices_found': len(devices),
                'verification_passed': True,
                'device_details': devices
            }
        except Exception as e:
            logger.error(f"Error in anti-spoofing verification: {e}")
            return {
                'spoofing_detected': False,
                'reason': f'Verification error: {str(e)}',
                'verification_passed': True,
                'error': str(e)
            }


