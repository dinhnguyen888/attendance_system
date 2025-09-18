"""
Face recognition service - keeps public API, delegates to modular services.
"""
from typing import Dict, Any
import numpy as np
import cv2

from app.services.registration_service import RegistrationService
from app.services.verification_service import VerificationService
from app.services.management_service import ManagementService


class FaceRecognitionService:
    """Facade that preserves existing methods while delegating to sub-services."""

    def __init__(self) -> None:
        self._registration = RegistrationService()
        self._verification = VerificationService()
        self._management = ManagementService()

    def register_employee_face_augmented(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        return self._registration.register_employee_face_augmented(employee_id, face_image_file, action)

    def register_employee_face(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        return self._registration.register_employee_face(employee_id, face_image_file, action)

    def verify_employee_face_max_similarity(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        return self._verification.verify_employee_face_max_similarity(employee_id, face_image_file, action)

    def verify_employee_face(self, employee_id: int, face_image_file, action: str) -> Dict[str, Any]:
        return self._verification.verify_employee_face(employee_id, face_image_file, action)

    def compare_two_faces(self, face_image1_file, face_image2_file) -> Dict[str, Any]:
        return self._management.compare_two_faces(face_image1_file, face_image2_file)

    def delete_employee_data(self, employee_id: int) -> Dict[str, Any]:
        return self._management.delete_employee_data(employee_id)
