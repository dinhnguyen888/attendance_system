# Face 3D Scan Web Application

A Vue.js application for face registration and verification with 3D face mesh visualization.

## Features

-   Face registration with 10-second video recording
-   Check-in/Check-out with 3-second video recording
-   Real-time face mesh visualization using MediaPipe
-   2x scale and center crop video recording
-   Video preview before submission
-   Responsive design with intuitive UI

## Technologies

-   Vue 3
-   TypeScript
-   MediaPipe Face Mesh
-   WebRTC for camera access
-   Face 3D Match API integration

## Components

### Services

-   `VideoRecordingService`: Handles video capture with scaling and cropping
-   `FaceMeshService`: Provides real-time face landmark detection
-   `ApiService`: Manages communication with the Face 3D Match API

### Pages

-   `FaceRegistrationPage`: Employee face registration with 10s video
-   `FaceVerificationPage`: Check-in/out verification with 3s video

## Setup

1. Install dependencies:

```bash
npm install
```

2. Start development server:

```bash
npm run dev
```

## Usage

### Face Registration

1. Enter Employee ID
2. Position face within the guide circle
3. Wait for face mesh detection
4. Click "Start Recording" for 10s video capture
5. Review recording and submit

### Face Verification

1. Select Check-in or Check-out
2. Position face within the guide circle
3. Wait for face mesh detection
4. Click "Start [Check-in/Check-out]" for 3s video capture
5. Review recording and submit

## Environment Variables

-   `VITE_API_URL`: Base URL for Face 3D Match API (default: http://localhost:8080)

## Browser Support

Requires browsers with:

-   WebRTC support
-   MediaRecorder API
-   Canvas API
