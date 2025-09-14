import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { ScanProgress } from '../types';
import styles from './FaceScanScreen.module.css';

interface FaceScanScreenProps {
  employeeId: string;
  onComplete: (videoBlob: Blob | any) => void;
  onCancel: () => void;
  mode?: 'register' | 'checkin' | 'checkout';
}

export const FaceScanScreen = ({ employeeId, onComplete, onCancel, mode = 'register' }: FaceScanScreenProps) => {
  const [scanProgress, setScanProgress] = useState<ScanProgress>({
    isScanning: false,
    progress: 0,
    phase: 'waiting'
  });
  
  const [countdown, setCountdown] = useState(3);
  const countdownRef = useRef<number | null>(null);
  
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [isFaceDetected, setIsFaceDetected] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | undefined>(undefined);
  const recordedChunksRef = useRef<Blob[]>([]);

  // Simple face detection using canvas
  const detectFace = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx || video.videoWidth === 0 || video.videoHeight === 0) {
      animationFrameRef.current = requestAnimationFrame(detectFace);
      return;
    }

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Simple face detection using image data analysis
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    
    // Check for skin tone pixels in center area
    let skinPixels = 0;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(canvas.width, canvas.height) / 4;
    
    // Sample every 8 pixels for performance
    for (let y = centerY - radius; y < centerY + radius; y += 8) {
      for (let x = centerX - radius; x < centerX + radius; x += 8) {
        if (x >= 0 && x < canvas.width && y >= 0 && y < canvas.height) {
          const index = (y * canvas.width + x) * 4;
          const r = data[index];
          const g = data[index + 1];
          const b = data[index + 2];
          
          // Simple skin tone detection
          if (r > 95 && g > 40 && b > 20 && 
              Math.max(r, g, b) - Math.min(r, g, b) > 15 && 
              Math.abs(r - g) > 15 && r > g && r > b) {
            skinPixels++;
          }
        }
      }
    }
    
    const faceDetected = skinPixels > 20;
    setIsFaceDetected(faceDetected);
    
    // Continue detection loop
    setTimeout(() => {
      animationFrameRef.current = requestAnimationFrame(detectFace);
    }, 100);
  };

  // Initialize camera
  useEffect(() => {
    const initCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user'
          }
        });
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setCameraStream(stream);
          
          videoRef.current.onloadedmetadata = () => {
            detectFace();
          };
        }
      } catch (error) {
        console.error('Error accessing camera:', error);
      }
    };

    initCamera();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  useEffect(() => {
    if (isFaceDetected && scanProgress.phase === 'waiting') {
      setScanProgress(prev => ({ ...prev, phase: 'face_detection' }));
    } else if (!isFaceDetected && scanProgress.phase === 'face_detection') {
      setScanProgress(prev => ({ ...prev, phase: 'waiting' }));
    }
  }, [isFaceDetected, scanProgress.phase]);

  const startCountdown = () => {
    // For checkin/checkout, skip hold_still phase and go directly to recording
    if (mode === 'checkin' || mode === 'checkout') {
      startScanning();
      return;
    }
    
    // For register mode, show hold_still phase first
    setScanProgress(prev => ({ ...prev, phase: 'hold_still' }));
    setCountdown(3);
    
    countdownRef.current = window.setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          if (countdownRef.current) {
            clearInterval(countdownRef.current);
          }
          startScanning();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const startScanning = async () => {
    if (!videoRef.current) return;

    // For checkin/checkout, don't show scanning animation, just record
    if (mode === 'checkin' || mode === 'checkout') {
      setScanProgress(prev => ({ ...prev, isScanning: true, phase: 'processing' }));
    } else {
      setScanProgress(prev => ({ ...prev, isScanning: true, phase: 'circle_scan' }));
    }

    // Start video recording
    const stream = videoRef.current.srcObject as MediaStream;
    const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
    
    // Clear previous chunks
    recordedChunksRef.current = [];
    
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunksRef.current.push(event.data);
      }
    };

    recorder.onstop = () => {
      if (recordedChunksRef.current.length > 0) {
        const videoBlob = new Blob(recordedChunksRef.current, { type: 'video/webm' });
        console.log('Video blob created:', videoBlob.size, 'bytes');
        
        if (mode === 'register') {
          onComplete(videoBlob);
        } else {
          // For checkin/checkout, process the video directly
          processVideo(videoBlob);
        }
      } else {
        console.error('No video chunks recorded');
        onCancel();
      }
    };

    setMediaRecorder(recorder);
    recorder.start();

    // Different recording duration based on mode
    const recordingDuration = mode === 'register' ? 15000 : 3000;
    
    setTimeout(() => {
      setScanProgress(prev => ({ ...prev, phase: 'complete' }));
      // Small delay to ensure all data is available
      setTimeout(() => {
        if (recorder.state === 'recording') {
          recorder.stop();
        }
      }, 100);
    }, recordingDuration);
  };

  const processVideo = async (videoBlob: Blob) => {
    setScanProgress(prev => ({ ...prev, phase: 'processing' }));
    
    try {
      // Import apiService dynamically to avoid circular imports
      const { apiService } = await import('../services/api');
      
      console.log(`🚀 Starting ${mode} flow with unified API...`);
      
      let result;
      if (mode === 'checkin') {
        result = await apiService.checkIn({
          employeeId,
          videoBlob,
          type: 'checkin'
        });
      } else if (mode === 'checkout') {
        result = await apiService.checkOut({
          employeeId,
          videoBlob,
          type: 'checkout'
        });
      } else {
        throw new Error('Invalid mode for processVideo');
      }
      
      if (result.success) {
        setScanProgress(prev => ({ ...prev, phase: 'complete' }));
        setTimeout(() => {
          onComplete(result);
        }, 2000);
      } else {
        throw new Error(result.error || 'Processing failed');
      }
    } catch (error) {
      console.error('Error processing video:', error);
      alert(`Lỗi: ${error instanceof Error ? error.message : 'Unknown error'}`);
      onCancel();
    }
  };

  const handleCancel = () => {
    // Stop recording if in progress
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
    
    // Stop countdown if in progress
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
    }
    
    // Stop camera stream
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
    }
    
    // Stop face detection animation
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    // Reset all states
    setScanProgress({
      isScanning: false,
      progress: 0,
      phase: 'waiting'
    });
    setIsFaceDetected(false);
    setMediaRecorder(null);
    setCountdown(3);
    recordedChunksRef.current = [];
    
    // Reload page for clean state
    window.location.reload();
  };

  return (
    <div className={styles.faceScanScreen}>
      {/* Cancel button */}
      <button className={styles.cancelBtn} onClick={handleCancel}>
        Cancel
      </button>

      {/* Main scanning area */}
      <div className={styles.scanningArea}>
        {/* Video container */}
        <div className={styles.videoContainer}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={styles.videoFeed}
          />
          <canvas
            ref={canvasRef}
            className={styles.faceMeshOverlay}
          />
        </div>

        {/* Progress circle - outer ring */}
        <div className={styles.progressCircleContainer}>
          <motion.div
            className={styles.progressCircle}
            animate={{
              rotate: scanProgress.isScanning ? 360 : 0,
            }}
            transition={{
              duration: 15,
              ease: "linear",
              repeat: scanProgress.isScanning ? 0 : 0
            }}
          >
            <svg viewBox="0 0 100 100" className={styles.progressSvg}>
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="rgba(0, 255, 0, 0.3)"
                strokeWidth="2"
              />
              <motion.circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#00ff00"
                strokeWidth="2"
                strokeLinecap="round"
                strokeDasharray="283"
                strokeDashoffset={283 - (scanProgress.progress * 283)}
                initial={{ strokeDashoffset: 283 }}
              />
            </svg>
          </motion.div>
        </div>

        {/* Animated scanning circle - only show for register mode */}
        {scanProgress.isScanning && mode === 'register' && (
          <div className={styles.scanningCircle} />
        )}

      </div>

      {/* Instructions */}
      <div className={styles.instructions}>
        <AnimatePresence mode="wait">
          {scanProgress.phase === 'waiting' && (
            <motion.p
              key="waiting"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={styles.instructionText}
            >
              Đặt khuôn mặt bạn vào trong vòng tròn
            </motion.p>
          )}
          
          {scanProgress.phase === 'face_detection' && (
            <motion.div
              key="face-detected"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={styles.faceDetected}
            >
              <p className={styles.instructionText}>Đã phát hiện khuôn mặt! Sẵn sàng quét</p>
              <button 
                className={styles.startScanBtn}
                onClick={startCountdown}
              >
                Bắt đầu quét
              </button>
            </motion.div>
          )}
          
          {scanProgress.phase === 'hold_still' && mode === 'register' && (
            <motion.div
              key="hold-still"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={styles.holdStill}
            >
              <p className={styles.instructionText}>Giữ yên khuôn mặt trong</p>
              <motion.div
                key={countdown}
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 1.5, opacity: 0 }}
                className={styles.countdownNumber}
              >
                {countdown}
              </motion.div>
              <p className={styles.instructionText}>giây...</p>
            </motion.div>
          )}
          
          {scanProgress.phase === 'circle_scan' && (
            <motion.p
              key="scanning"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={styles.instructionText}
            >
              {mode === 'register' 
                ? 'Di chuyển đầu từ từ để hoàn thành vòng tròn trong 15 giây'
                : 'Đang quay video...'
              }
            </motion.p>
          )}
          
          {scanProgress.phase === 'processing' && (
            <motion.p
              key="processing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={styles.instructionText}
            >
              Đang xử lý...
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};