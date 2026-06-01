import logging
from typing import Dict, List, Tuple
import numpy as np


logger = logging.getLogger(__name__)
YOLO_MODEL = "yolo11n.pt"


class YOLOv11DeviceDetector:
    """Detect presentation devices with YOLO."""

    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.device_classes = {}
        self._load_model_with_progress()

    def _load_model_with_progress(self):
        try:
            from ultralytics import YOLO
            logger.info("Loading %s weights...", YOLO_MODEL)
            self.model = YOLO(YOLO_MODEL)
            self.device_classes = {}
            for class_id, class_name in self.model.names.items():
                lower = class_name.lower()
                if any(k in lower for k in ["phone", "cell", "mobile"]):
                    self.device_classes["phone"] = class_id
                if "laptop" in lower or "computer" in lower:
                    self.device_classes["laptop"] = class_id
                if "tablet" in lower:
                    self.device_classes["tablet"] = class_id
            self.model_loaded = True
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")
            self.model = None
            self.device_classes = {}
            self.model_loaded = False

    def detect_devices(self, image: np.ndarray, confidence_threshold: float = 0.4) -> List[Dict]:
        if not self.model_loaded:
            return []
        try:
            results = self.model(image, conf=0.1, verbose=False)
            detected = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                for i in range(len(boxes)):
                    class_id = int(boxes.cls[i])
                    conf = float(boxes.conf[i])
                    if class_id not in self.device_classes.values():
                        continue
                    x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
                    detected.append({
                        'class_name': next((n for n, cid in self.device_classes.items() if cid == class_id), f'device_{class_id}'),
                        'class_id': class_id,
                        'confidence': conf,
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'width': int(x2 - x1),
                        'height': int(y2 - y1),
                        'area': int((x2 - x1) * (y2 - y1))
                    })
            detected.sort(key=lambda x: x['area'], reverse=True)
            return detected
        except Exception:
            return []

    def is_device_dominant(self, device_bbox: List[int], image_shape: Tuple[int, int], area_threshold: float) -> bool:
        """Check whether a detected device dominates the frame."""
        try:
            h, w = image_shape[:2]
            total_area = max(1, h * w)
            x1, y1, x2, y2 = device_bbox
            device_area = max(0, (x2 - x1) * (y2 - y1))
            area_ratio = device_area / total_area
            return area_ratio >= area_threshold
        except Exception:
            return False


