// Face Recognition API Service
class FaceAPI {
  constructor() {
    this.baseURL = '/api';
    this.mediaRecorder = null;
    this.recordedChunks = [];
    this.recordingTime = 0;
    this.recordingInterval = null;
  }

  // Helper method to handle API requests
  async _makeRequest(url, method = 'GET', data = null, isJson = true) {
    const options = {
      method,
      headers: {}
    };

    if (data) {
      if (data instanceof FormData) {
        options.body = data;
      } else {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(data);
      }
    }

    try {
      const response = await fetch(`${this.baseURL}${url}`, options);
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`API request failed: ${error}`);
      }
      
      return isJson ? await response.json() : await response.blob();
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }

  // Register a new employee with face data
  async registerEmployee(employeeId, videoBlob) {
    const formData = new FormData();
    formData.append('employee_id', employeeId);
    formData.append('video', videoBlob, 'registration.mp4');
    
    return this._makeRequest('/register', 'POST', formData, false);
  }

  // Upload 3x4 photo for an employee
  async upload3x4Photo(employeeId, photoBlob) {
    const formData = new FormData();
    formData.append('employee_id', employeeId);
    formData.append('photo', photoBlob, 'photo_3x4.jpg');
    
    return this._makeRequest('/upload-3x4', 'POST', formData, false);
  }

  // Check-in an employee
  async checkIn(videoBlob) {
    const formData = new FormData();
    formData.append('video', videoBlob, 'checkin.mp4');
    
    return this._makeRequest('/check-in', 'POST', formData, true);
  }

  // Check-out an employee
  async checkOut(videoBlob) {
    const formData = new FormData();
    formData.append('video', videoBlob, 'checkout.mp4');
    
    return this._makeRequest('/check-out', 'POST', formData, true);
  }

  // Start recording video from a video element
  startRecording(videoElement, onTimeUpdate, onStop) {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.stopRecording();
    }

    this.recordedChunks = [];
    
    try {
      const stream = videoElement.srcObject;
      if (!stream) {
        throw new Error('No video stream available');
      }

      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm;codecs=vp9',
        videoBitsPerSecond: 2500000 // 2.5Mbps
      });

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.recordedChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
        this.recordedChunks = [];
        
        // Reset timer
        this.recordingTime = 0;
        clearInterval(this.recordingInterval);
        this.recordingInterval = null;
        
        if (onStop) onStop(blob);
      };

      // Start recording
      this.mediaRecorder.start(100); // Collect data every 100ms
      this.recordingTime = 0;
      
      // Update timer every second
      this.recordingInterval = setInterval(() => {
        this.recordingTime++;
        if (onTimeUpdate) onTimeUpdate(this.recordingTime);
      }, 1000);
      
      return true;
    } catch (error) {
      console.error('Error starting recording:', error);
      return false;
    }
  }

  // Stop recording
  stopRecording() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }
    
    // Stop all tracks in the stream
    if (this.mediaRecorder && this.mediaRecorder.stream) {
      this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    
    clearInterval(this.recordingInterval);
    this.recordingInterval = null;
    this.recordingTime = 0;
  }

  // Initialize camera
  async initCamera(videoElement, facingMode = 'user') {
    try {
      const constraints = {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 960 },
          facingMode: facingMode,
          aspectRatio: 4/3
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      videoElement.srcObject = stream;
      
      return new Promise((resolve) => {
        videoElement.onloadedmetadata = () => {
          videoElement.play();
          resolve(stream);
        };
      });
    } catch (error) {
      console.error('Error accessing camera:', error);
      throw error;
    }
  }

  // Stop camera
  stopCamera(videoElement) {
    if (videoElement.srcObject) {
      const tracks = videoElement.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoElement.srcObject = null;
    }
  }

  // Capture a frame from video
  captureFrame(videoElement, type = 'image/jpeg', quality = 0.92) {
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext('2d');
    
    // Draw the current frame from the video on the canvas
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to blob
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob);
      }, type, quality);
    });
  }
}

// Export a singleton instance
export const faceAPI = new FaceAPI();
