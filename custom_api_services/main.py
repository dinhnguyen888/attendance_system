"""
Face Recognition API - Refactored Main Application
"""
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

# Import controllers
from controllers.face_recognition_controller import (
    verify_face, 
    register_employee_face, 
    delete_employee_face, 
    compare_two_faces
)
from controllers.system_controller import (
    read_root,
    get_opencv_version,
    health_check,
    backfill_embeddings,
    get_api_info
)

# Import models for type hints
from models.schemas import *

# Initialize FastAPI app
app = FastAPI(title="Face Recognition API", version="2.0.0")

# CORS middleware để cho phép Odoo gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/")
def root():
    return read_root()

@app.get("/opencv-version")
def opencv_version():
    return get_opencv_version()

@app.post("/face-recognition/verify", response_model=FaceVerificationResponse)
async def verify_face_endpoint(
    face_image: UploadFile = File(...),
    action: str = Form(...),
    employee_id: int = Form(...)
):
    return await verify_face(face_image, action, employee_id)

@app.post("/face-recognition/register", response_model=FaceRegistrationResponse)
async def register_employee_face_endpoint(
    employee_id: int = Form(...),
    action: str = Form(...),
    face_image: UploadFile = File(...)
):
    return await register_employee_face(employee_id, action, face_image)

@app.delete("/face-recognition/employee/{employee_id}", response_model=DeleteEmployeeResponse)
async def delete_employee_face_endpoint(employee_id: int):
    return await delete_employee_face(employee_id)

@app.get("/face-recognition/health", response_model=HealthCheckResponse)
async def health_check_endpoint():
    return await health_check()

@app.post("/face-recognition/backfill-embeddings", response_model=BackfillEmbeddingsResponse)
async def backfill_embeddings_endpoint():
    return await backfill_embeddings()

@app.post("/face-recognition/compare", response_model=FaceComparisonResponse)
async def compare_two_faces_endpoint(
    face_image1: UploadFile = File(...),
    face_image2: UploadFile = File(...)
):
    return await compare_two_faces(face_image1, face_image2)

@app.get("/face-recognition/info", response_model=APIInfoResponse)
async def get_api_info_endpoint():
    return await get_api_info()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
