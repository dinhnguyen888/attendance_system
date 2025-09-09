"""
New main application file using the refactored structure
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.routes import router
from app.config import API_TITLE, API_VERSION

# Create FastAPI app
app = FastAPI(title=API_TITLE, version=API_VERSION)

# CORS middleware to allow Odoo to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, should limit to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main_new:app", host="0.0.0.0", port=8000, reload=True)
