"""
YOLOv11n Device Detection Module for Anti-Spoofing
Detects smartphones, laptops, tablets, and monitors to prevent presentation attacks
"""
import cv2
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
from pathlib import Path
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YOLOv11DeviceDetector:
    """YOLOv11n-based device detector for anti-spoofing verification"""
    
    def __init__(self):
        """Initialize YOLOv11n model"""
        self.model = None
        self.model_loaded = False
        self.device_classes = {}
        
        # Load YOLO11n model with progress bar
        self._load_model_with_progress()
    
    def _load_model_with_progress(self):
        """Load YOLO11n model with visual progress bar - SYNCHRONOUS"""
        try:
            logger.info("🤖 Starting YOLO model loading...")
            
            # Step 1: Import dependencies
            logger.info("📦 Importing YOLO framework...")
            from ultralytics import YOLO
            import torch
            
            # Step 2: Load YOLO11n model with auto-download
            logger.info("⚡ Loading YOLO11n weights...")
            
            try:
                # YOLO11n will auto-download if not available
                logger.info("📥 Loading YOLO11n (auto-download if needed)...")
                self.model = YOLO('yolo11n.pt')
                logger.info("✅ Successfully loaded YOLO11n")
            except Exception as e:
                logger.warning(f"⚠️ YOLO11n failed, trying YOLOv8n fallback: {e}")
                # Fallback to YOLOv8n if YOLO11n not supported
                self.model = YOLO('yolov8n.pt')
                logger.info("✅ Successfully loaded YOLOv8n as fallback")
            
            # Step 3: Initialize device classes and check actual YOLO class names
            logger.info("🔧 Setting up device classes...")
            
            # Get actual YOLO class names
            yolo_classes = self.model.names
            logger.info(f"📋 Available YOLO classes: {yolo_classes}")
            
            # Map device-related classes dynamically including picture/photo
            device_keywords = ['tv', 'laptop', 'phone', 'picture', 'photo', 'book']
            device_related = {}
            for class_id, class_name in self.model.names.items():
                for keyword in device_keywords:
                    if keyword in class_name.lower():
                        if keyword == 'phone':
                            self.device_classes['phone'] = class_id
                        elif keyword in ['picture', 'photo']:
                            self.device_classes['picture'] = class_id
                        elif keyword == 'book':  # Books can be used for photo spoofing
                            self.device_classes['book'] = class_id
                        else:
                            self.device_classes[keyword] = class_id
                        device_related[class_name] = class_id
            
            logger.info(f"🎯 Device-related classes found: {device_related}")
            
            # Set up device classes based on what's actually available
            # self.device_classes = {}
            
            # Look for phone variants
            for class_name, class_id in device_related.items():
                if 'phone' in class_name.lower() or 'cell' in class_name.lower() or 'mobile' in class_name.lower():
                    self.device_classes['phone'] = class_id
                elif 'laptop' in class_name.lower() or 'computer' in class_name.lower():
                    self.device_classes['laptop'] = class_id
                elif 'tv' in class_name.lower() or 'monitor' in class_name.lower():
                    self.device_classes['tv'] = class_id
                elif 'tablet' in class_name.lower():
                    self.device_classes['tablet'] = class_id
            
            # Fallback to standard COCO IDs if not found
            if not self.device_classes:
                self.device_classes = {
                    'cell phone': 67,  # Standard COCO class ID
                    'laptop': 63,      # Standard COCO class ID  
                    'tv': 62,          # Standard COCO class ID
                }
            
            logger.info(f"✅ Final device classes mapping: {self.device_classes}")
            
            # Step 4: Complete
            logger.info("✅ YOLO model loaded successfully and ready for detection")
            self.model_loaded = True
            
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {e}")
            logger.warning("⚠️ Device detection will be disabled")
            self.model = None
            self.device_classes = {}
            self.model_loaded = False
    
    def detect_devices(self, image: np.ndarray, confidence_threshold: float = 0.4) -> List[Dict]:
        """
        Detect devices in the image using YOLO11n
        
        Args:
            image: Input image as numpy array (BGR format)
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            List of detected devices with bounding boxes and metadata
        """
        if not self.model_loaded:
            logger.warning("YOLO11n model not loaded, skipping device detection")
            return []
        
        try:
            logger.info(f"🔍 Running YOLO11n inference on image shape: {image.shape}")
            
            # Run YOLO inference with very low confidence for maximum detection
            results = self.model(image, conf=0.1, verbose=False)  # Very low threshold for phones
            
            logger.info(f"📊 YOLO11n inference completed, got {len(results)} result(s)")
            
            detected_devices = []
            all_detections = []  # For debugging
            
            for result in results:
                logger.info(f"🎯 Processing result with boxes: {result.boxes is not None}")
                boxes = result.boxes
                if boxes is not None:
                    logger.info(f"📦 Found {len(boxes)} total detections")
                    for i in range(len(boxes)):
                        class_id = int(boxes.cls[i])
                        confidence = float(boxes.conf[i])
                        
                        # Log all detections for debugging
                        class_name = result.names[class_id] if hasattr(result, 'names') else f"class_{class_id}"
                        all_detections.append(f"{class_name}({class_id}): {confidence:.3f}")
                        
                        logger.info(f"🔎 Detection {i+1}: {class_name} (ID: {class_id}) confidence: {confidence:.3f}")
                        
                        # Check if detected object is a target device
                        if class_id in self.device_classes.values():
                            # Get bounding box coordinates (xyxy format)
                            x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
                            
                            # Calculate area
                            width = x2 - x1
                            height = y2 - y1
                            area = width * height
                            
                            # Find device name by class_id
                            device_name = None
                            for name, cid in self.device_classes.items():
                                if cid == class_id:
                                    device_name = name
                                    break
                            
                            device_info = {
                                'class_name': device_name or f"device_{class_id}",
                                'class_id': class_id,
                                'confidence': confidence,
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'width': int(width),
                                'height': int(height),
                                'area': int(area)
                            }
                            detected_devices.append(device_info)
            
            # Log all detections for debugging
            if all_detections:
                logger.info(f"🔍 YOLO11n found {len(all_detections)} total objects: {all_detections}")
            else:
                logger.warning("⚠️ YOLO11n found NO objects in the image!")
            
            # Log device class mapping for debugging
            logger.info(f"🎯 Looking for device classes: {self.device_classes}")
            
            # Sort devices by area (largest first)
            detected_devices.sort(key=lambda x: x['area'], reverse=True)
            
            if detected_devices:
                logger.info(f"✅ YOLO11n detected {len(detected_devices)} target devices: {[d['class_name'] for d in detected_devices]}")
            else:
                logger.warning(f"❌ No target devices found! Total detections: {len(all_detections)}")
            
            return detected_devices
            
        except Exception as e:
            logger.error(f"Error in YOLO11n device detection: {e}")
            return []
    
    def crop_device_region(self, image: np.ndarray, bbox: List[int], margin: int = 5) -> np.ndarray:
        """
        Crop device region from image
        
        Args:
            image: Input image
            bbox: Bounding box [x1, y1, x2, y2]
            margin: Additional margin around bounding box
            
        Returns:
            Cropped device region
        """
        try:
            h, w = image.shape[:2]
            x1, y1, x2, y2 = bbox
            
            # Add margin and ensure within image bounds
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(w, x2 + margin)
            y2 = min(h, y2 + margin)
            
            cropped = image[y1:y2, x1:x2]
            logger.info(f"Cropped device region: {cropped.shape}")
            return cropped
            
        except Exception as e:
            logger.error(f"Error cropping device region: {e}")
            return image
    
    def is_device_dominant(self, device_bbox: List[int], image_shape: Tuple[int, int], 
                          area_threshold: float = 0.25) -> bool:
        """
        Check if device occupies dominant area in the frame
        
        Args:
            device_bbox: Device bounding box [x1, y1, x2, y2]
            image_shape: Image dimensions (height, width)
            area_threshold: Minimum area ratio to consider dominant
            
        Returns:
            True if device is dominant in frame
        """
        try:
            h, w = image_shape[:2]
            total_area = h * w
            
            x1, y1, x2, y2 = device_bbox
            device_area = (x2 - x1) * (y2 - y1)
            area_ratio = device_area / total_area
            
            is_dominant = area_ratio >= area_threshold
            logger.info(f"Device area ratio: {area_ratio:.3f}, dominant: {is_dominant}")
            return is_dominant
            
        except Exception as e:
            logger.error(f"Error checking device dominance: {e}")
            return False


class FaceInDeviceChecker:
    """Enhanced checker for face-in-device detection with screen activity analysis and distance comparison"""
    
    def __init__(self):
        """Initialize face detector for device screen analysis"""
        try:
            from insightface.app import FaceAnalysis
            self.face_detector = FaceAnalysis()
            self.face_detector.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace detector initialized for face-in-device check")
        except Exception as e:
            logger.error(f"Failed to initialize face detector: {e}")
            self.face_detector = None
    
    def _estimate_face_distance(self, face_bbox: List[int], image_shape: tuple) -> float:
        """
        Estimate face distance based on face size in image
        Larger face = closer distance, smaller face = farther distance
        
        Args:
            face_bbox: [x, y, w, h] face bounding box
            image_shape: (height, width, channels) of image
            
        Returns:
            Estimated distance (arbitrary units, smaller = closer)
        """
        try:
            face_x, face_y, face_w, face_h = face_bbox
            face_area = face_w * face_h
            image_area = image_shape[0] * image_shape[1]
            
            # Face area ratio to image - larger ratio means closer face
            face_ratio = face_area / image_area
            
            # Convert to distance estimate (inverse relationship)
            # Closer face (larger ratio) = smaller distance value
            distance_estimate = 1.0 / (face_ratio + 0.001)  # Add small value to avoid division by zero
            
            return distance_estimate
            
        except Exception as e:
            logger.error(f"Error estimating face distance: {e}")
            return float('inf')  # Return very large distance on error

    def check_face_in_device(self, image: np.ndarray, device_bbox: List[int]) -> Dict:
        """
        Check if detected face is within device screen area with improved logic
        
        Args:
            image: Input image
            device_bbox: Device bounding box [x1, y1, x2, y2]
            
        Returns:
            Detection result with face location and overlap analysis
        """
        if self.face_detector is None:
            return {
                'face_in_device': False, 
                'error': 'Face detector not available'
            }
        
        try:
            # Step 1: Crop device region first to focus detection
            device_region = self._crop_device_region(image, device_bbox)
            
            # Step 2: Check if device screen is likely active (not black screen)
            is_active_screen = self._is_active_screen(device_region)
            
            if not is_active_screen:
                logger.info("Device screen appears inactive/black - likely no face display")
                return {
                    'face_in_device': False,
                    'reason': 'Device screen appears inactive/black',
                    'screen_active': False,
                    'face_count': 0
                }
            
            # Step 3: Detect faces in the device region only
            faces = self.face_detector.get(device_region)
            
            if len(faces) == 0:
                return {
                    'face_in_device': False,
                    'reason': 'No face detected in device screen area',
                    'face_count': 0,
                    'screen_active': True
                }
            
            # Step 4: Check if face is significant size (not just noise/reflection)
            # Convert InsightFace format to (x, y, w, h)
            face_bboxes = []
            for face in faces:
                bbox = face.bbox.astype(int)
                x, y, x2, y2 = bbox
                w, h = x2 - x, y2 - y
                face_bboxes.append((x, y, w, h))
            
            largest_face = max(face_bboxes, key=lambda f: f[2] * f[3])  # w * h
            face_x, face_y, face_w, face_h = largest_face
            
            # Convert back to full image coordinates
            dx1, dy1, dx2, dy2 = device_bbox
            full_face_bbox = [dx1 + face_x, dy1 + face_y, dx1 + face_x + face_w, dy1 + face_y + face_h]
            
            # Step 5: Check face quality and size
            face_area = face_w * face_h
            device_area = (dx2 - dx1) * (dy2 - dy1)  # Fixed: dy2 - dy1, not dy1 - dy2
            face_to_device_ratio = face_area / device_area if device_area > 0 else 0
            
            # Face should be significant portion of device screen (lowered to >2% for maximum sensitivity)
            is_significant_face = face_to_device_ratio > 0.02
            
            # Step 6: Face size comparison for spoofing detection
            # Get all faces in the full image for size comparison
            all_faces = self.face_detector.get(image)
            external_faces = []
            
            # Find faces outside the device area (employee faces)
            for face in all_faces:
                face_bbox_full = face.bbox.astype(int)  # [x1, y1, x2, y2]
                face_x1, face_y1, face_x2, face_y2 = face_bbox_full
                
                # Check if this face is outside device area
                dx1, dy1, dx2, dy2 = device_bbox
                if not (face_x1 >= dx1 and face_y1 >= dy1 and face_x2 <= dx2 and face_y2 <= dy2):
                    face_area_external = (face_x2 - face_x1) * (face_y2 - face_y1)
                    external_faces.append(face_area_external)
            
            # Calculate face sizes
            device_face_area = face_w * face_h
            size_spoofing_detected = False
            size_ratio = 1.0
            
            if external_faces:
                # Find largest external face (employee face)
                largest_external_face_area = max(external_faces)
                
                # If device face is smaller than employee face, it's likely another person's phone
                size_ratio = device_face_area / largest_external_face_area
                size_spoofing_detected = size_ratio < 0.8  # Device face is 20% smaller than employee
                
                logger.info(f"Size analysis - Device face area: {device_face_area}, Employee face area: {largest_external_face_area}, Ratio: {size_ratio:.2f}")
                
                if size_spoofing_detected:
                    logger.info("Phone face smaller than employee face - likely another person's phone, PASS")
            
            # Step 7: Final decision with size check
            face_in_device = is_significant_face and is_active_screen and not size_spoofing_detected
            
            result = {
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
            
            logger.info(f"Enhanced face in device check: {face_in_device}, "
                       f"screen_active: {is_active_screen}, "
                       f"face_ratio: {face_to_device_ratio:.3f}, "
                       f"size_spoofing: {size_spoofing_detected}")
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced face-in-device detection: {e}")
            return {
                'face_in_device': False, 
                'error': str(e)
            }
    
    def _crop_device_region(self, image: np.ndarray, device_bbox: List[int]) -> np.ndarray:
        """Crop device region from image for focused analysis"""
        try:
            x1, y1, x2, y2 = device_bbox
            h, w = image.shape[:2]
            
            # Ensure coordinates are within image bounds
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            return image[y1:y2, x1:x2]
        except Exception as e:
            logger.error(f"Error cropping device region: {e}")
            return image
    
    def _is_active_screen(self, device_region: np.ndarray) -> bool:
        """
        Check if device screen appears active (not black/dark)
        
        Args:
            device_region: Cropped device screen area
            
        Returns:
            True if screen appears active with content
        """
        try:
            if device_region.size == 0:
                return False
            
            # Convert to grayscale for analysis
            if len(device_region.shape) == 3:
                gray = cv2.cvtColor(device_region, cv2.COLOR_BGR2GRAY)
            else:
                gray = device_region
            
            # Calculate brightness statistics
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            
            # Check for variation in brightness (indicates content)
            has_variation = std_brightness > 15  # Threshold for content variation
            is_bright_enough = mean_brightness > 30  # Not completely dark
            
            # Check for edges (indicates content/structure)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            has_edges = edge_density > 0.01  # At least 1% edges
            
            is_active = (has_variation and is_bright_enough) or has_edges
            
            logger.info(f"Screen analysis - brightness: {mean_brightness:.1f}, "
                       f"variation: {std_brightness:.1f}, edges: {edge_density:.3f}, "
                       f"active: {is_active}")
            
            return is_active
            
        except Exception as e:
            logger.error(f"Error analyzing screen activity: {e}")
            return True  # Default to active if analysis fails
    
    def _calculate_bbox_overlap(self, face_bbox: List[int], device_bbox: List[int]) -> float:
        """
        Calculate overlap ratio between face and device bounding boxes
        
        Args:
            face_bbox: Face bounding box [x1, y1, x2, y2]
            device_bbox: Device bounding box [x1, y1, x2, y2]
            
        Returns:
            Overlap ratio (intersection area / face area)
        """
        try:
            fx1, fy1, fx2, fy2 = face_bbox
            dx1, dy1, dx2, dy2 = device_bbox
            
            # Calculate intersection rectangle
            ix1 = max(fx1, dx1)
            iy1 = max(fy1, dy1)
            ix2 = min(fx2, dx2)
            iy2 = min(fy2, dy2)
            
            # No intersection
            if ix1 >= ix2 or iy1 >= iy2:
                return 0.0
            
            # Calculate areas
            intersection_area = (ix2 - ix1) * (iy2 - iy1)
            face_area = (fx2 - fx1) * (fy2 - fy1)
            
            # Return overlap ratio
            overlap_ratio = intersection_area / face_area if face_area > 0 else 0.0
            return overlap_ratio
            
        except Exception as e:
            logger.error(f"Error calculating bbox overlap: {e}")
            return 0.0


class AntiSpoofingVerifier:
    """Main anti-spoofing verification using YOLOv11n device detection"""
    
    def __init__(self):
        """Initialize device detector and face checker"""
        self.device_detector = YOLOv11DeviceDetector()
        self.face_checker = FaceInDeviceChecker()
        logger.info("Anti-spoofing verifier initialized")
    
    def verify_no_device_spoofing(self, image: np.ndarray) -> Dict:
        """
        Main verification function to detect device-based spoofing
        
        Args:
            image: Input image for verification
            
        Returns:
            Verification result with spoofing detection status
        """
        try:
            logger.info("Starting device-based anti-spoofing verification")
            
            # Check if YOLOv11n model is loaded
            if not self.device_detector.model_loaded:
                logger.warning("YOLOv11n model not loaded - attempting to reload...")
                self.device_detector._load_model_with_progress()
                
                if not self.device_detector.model_loaded:
                    logger.error("Failed to load YOLOv11n model - anti-spoofing disabled")
                    return {
                        'spoofing_detected': False,
                        'reason': 'YOLOv11n model unavailable - verification skipped',
                        'verification_passed': True,
                        'model_error': True
                    }
            
            # Step 1: Detect devices using YOLO with very low threshold for better detection
            devices = self.device_detector.detect_devices(image, confidence_threshold=0.15)  # Much lower threshold
            
            if not devices:
                logger.warning("⚠️ NO DEVICES DETECTED - This might be the issue!")
                logger.info("📝 Possible reasons: 1) No phone in frame, 2) YOLO confidence too high, 3) Model not detecting phones properly")
                return {
                    'spoofing_detected': False,
                    'reason': 'No devices detected in frame',
                    'devices_found': 0,
                    'verification_passed': True
                }
            
            # Step 2: Check each detected device
            for device in devices:
                device_name = device['class_name']
                device_bbox = device['bbox']
                device_confidence = device['confidence']
                
                logger.info(f"Analyzing {device_name} (confidence: {device_confidence:.3f})")
                
                # Step 3: Check if face is within device screen
                face_check = self.face_checker.check_face_in_device(image, device_bbox)
                
                if face_check.get('face_in_device', False):
                    # SPOOFING DETECTED - No need to check dominance, any face in device is suspicious
                    logger.warning(f"🚨 SPOOFING DETECTED: Face found in {device_name}!")
                    return {
                        'spoofing_detected': True,
                        'spoofing_type': 'device_presentation_attack',
                        'spoofing_device': device_name,
                        'device_confidence': device_confidence,
                        'face_overlap_ratio': face_check.get('overlap_ratio', 0),
                        'face_to_device_ratio': face_check.get('face_to_device_ratio', 0),
                        'reason': f'Khuôn mặt phát hiện trong màn hình {device_name} - có thể là tấn công giả mạo' + 
                                 (f' (khuôn mặt trong điện thoại nhỏ hơn {face_check.get("size_ratio", 1):.1f}x so với nhân viên)' 
                                  if face_check.get('size_spoofing_detected', False) else ''),
                        'verification_passed': False,
                        'devices_found': len(devices)
                    }
            
            # No spoofing detected
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
                'verification_passed': True,  # Allow verification to continue on error
                'error': str(e)
            }
    
    def create_spoofing_report(self, verification_result: Dict) -> str:
        """Create human-readable spoofing detection report"""
        try:
            report = []
            report.append("=== YOLOv11n ANTI-SPOOFING REPORT ===")
            
            if verification_result['spoofing_detected']:
                report.append("🚨 SPOOFING DETECTED")
                report.append(f"Device: {verification_result.get('spoofing_device', 'Unknown')}")
                report.append(f"Confidence: {verification_result.get('device_confidence', 0):.3f}")
                report.append(f"Face Overlap: {verification_result.get('face_overlap_ratio', 0):.3f}")
                report.append(f"Reason: {verification_result.get('reason', 'Unknown')}")
            else:
                report.append("✅ NO SPOOFING DETECTED")
                report.append(f"Devices Found: {verification_result.get('devices_found', 0)}")
                report.append(f"Reason: {verification_result.get('reason', 'Clean verification')}")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"Error creating report: {str(e)}"
