from fastapi import FastAPI
import cv2

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application with OpenCV"}

@app.get("/opencv-version")
def get_opencv_version():
    return {"opencv_version": cv2.__version__}