"""
Data models and schemas for face recognition API
"""
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class ActionType(str, Enum):
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    REGISTER = "register"

class FaceVerificationRequest(BaseModel):
    employee_id: int
    action: ActionType

class FaceRegistrationRequest(BaseModel):
    employee_id: int
    action: ActionType = ActionType.REGISTER

class FaceVerificationResponse(BaseModel):
    success: bool
    message: str
    confidence: float
    employee_id: int

class FaceRegistrationResponse(BaseModel):
    success: bool
    message: str
    employee_id: Optional[int] = None
    confidence: float = 0.0

class FaceComparisonResponse(BaseModel):
    success: bool
    message: str
    similarity: float
    is_same_person: Optional[bool] = None
    confidence: Optional[float] = None
    threshold: Optional[float] = None

class HealthCheckResponse(BaseModel):
    status: str
    opencv_version: str
    employee_faces_count: int
    insightface: bool
    cosine_threshold: float
    embedding_model: Optional[str] = None
    embedding_files: Optional[int] = None
    embedding_samples: Optional[int] = None

class DeleteEmployeeResponse(BaseModel):
    success: bool
    message: str
    employee_id: int
    deleted_files: List[str]
    errors: List[str]

class BackfillEmbeddingsResponse(BaseModel):
    success: bool
    processed: Optional[int] = None
    created: Optional[int] = None
    failed: Optional[List[dict]] = None
    embedding_files: Optional[int] = None
    error: Optional[str] = None

class APIInfoResponse(BaseModel):
    api_name: str
    version: str
    workflow: dict
    features: dict
    endpoints: dict
