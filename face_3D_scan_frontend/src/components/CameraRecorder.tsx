import React, { useRef, useState, useCallback, useEffect } from 'react';
import type { RecordingState } from '../types';

interface CameraRecorderProps {
  onRecordingComplete: (blob: Blob) => void;
  onError: (error: string) => void;
}

export const CameraRecorder: React.FC<CameraRecorderProps> = ({ onRecordingComplete, onError }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const intervalRef = useRef<number | null>(null);

  const [recordingState, setRecordingState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    duration: 0,
    blob: null,
  });

  const [hasPermission, setHasPermission] = useState<boolean | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        },
        audio: false
      });
      
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setHasPermission(true);
    } catch (error) {
      console.error('Error accessing camera:', error);
      setHasPermission(false);
      onError('Không thể truy cập camera. Vui lòng cho phép quyền truy cập camera.');
    }
  }, [onError]);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  const startRecording = useCallback(() => {
    if (!streamRef.current) return;

    try {
      let mimeType = 'video/mp4;codecs=h264';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'video/webm;codecs=vp9';
      }
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'video/webm';
      }
      
      const mediaRecorder = new MediaRecorder(streamRef.current, {
        mimeType: mimeType
      });
      
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setRecordingState(prev => ({ ...prev, blob }));
        onRecordingComplete(blob);
      };

      mediaRecorder.start(1000); // Collect data every second
      
      setRecordingState(prev => ({ 
        ...prev, 
        isRecording: true, 
        duration: 0 
      }));

      // Update duration every second
      intervalRef.current = setInterval(() => {
        setRecordingState(prev => ({ 
          ...prev, 
          duration: prev.duration + 1 
        }));
      }, 1000);

    } catch (error) {
      console.error('Error starting recording:', error);
      onError('Không thể bắt đầu ghi video');
    }
  }, [onRecordingComplete, onError]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState.isRecording) {
      mediaRecorderRef.current.stop();
      setRecordingState(prev => ({ 
        ...prev, 
        isRecording: false 
      }));
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, [recordingState.isRecording]);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [startCamera, stopCamera]);

  if (hasPermission === false) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Không thể truy cập camera. Vui lòng cho phép quyền truy cập camera và tải lại trang.</p>
        <button onClick={() => window.location.reload()}>
          Tải lại trang
        </button>
      </div>
    );
  }

  if (hasPermission === null) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Đang khởi tạo camera...</p>
      </div>
    );
  }

  return (
    <div style={{ textAlign: 'center', padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{ 
            width: '100%', 
            maxWidth: '640px', 
            height: 'auto',
            border: '2px solid #ccc',
            borderRadius: '8px'
          }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        {recordingState.isRecording && (
          <div style={{ 
            fontSize: '18px', 
            fontWeight: 'bold', 
            color: 'red',
            marginBottom: '10px'
          }}>
            🔴 Đang ghi: {formatDuration(recordingState.duration)}
          </div>
        )}
      </div>

      <div>
        {!recordingState.isRecording ? (
          <button
            onClick={startRecording}
            style={{
              padding: '12px 24px',
              fontSize: '16px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
          >
            Bắt đầu ghi video
          </button>
        ) : (
          <button
            onClick={stopRecording}
            style={{
              padding: '12px 24px',
              fontSize: '16px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Dừng ghi video
          </button>
        )}
      </div>

      {recordingState.blob && (
        <div style={{ marginTop: '20px' }}>
          <p>Video đã ghi thành công! ({Math.round(recordingState.blob.size / 1024)} KB)</p>
        </div>
      )}
    </div>
  );
};
