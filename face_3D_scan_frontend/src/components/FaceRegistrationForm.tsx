import React, { useState } from 'react';
import { CameraRecorder } from './CameraRecorder';
import { faceRegistrationApi } from '../services/api';

export const FaceRegistrationForm: React.FC = () => {
  const [employeeId, setEmployeeId] = useState('');
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRecordingComplete = (blob: Blob) => {
    setVideoBlob(blob);
    setError(null);
    setUploadResult(null);
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
  };

  const handleSubmit = async () => {
    if (!employeeId.trim()) {
      setError('Vui lòng nhập mã nhân viên');
      return;
    }

    if (!videoBlob) {
      setError('Vui lòng ghi video trước khi đăng ký');
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const videoFile = new File([videoBlob], `employee_${employeeId}.mp4`, {
        type: 'video/mp4'
      });

      const result = await faceRegistrationApi.registerFace(employeeId, videoFile);
      
      setUploadResult(`Đăng ký thành công! 
        - Video: ${result.video}
        - Frames: ${result.frames_dir}
        - Preprocess: ${result.preprocess_dir}
        - Embeddings: ${result.embedding_dir}`);
      
      // Reset form
      setVideoBlob(null);
      setEmployeeId('');
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Có lỗi xảy ra khi đăng ký');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setEmployeeId('');
    setVideoBlob(null);
    setError(null);
    setUploadResult(null);
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>
        Đăng ký khuôn mặt 3D
      </h1>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
          Mã nhân viên:
        </label>
        <input
          type="text"
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
          placeholder="Nhập mã nhân viên (VD: E001)"
          style={{
            width: '100%',
            padding: '10px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            fontSize: '16px'
          }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Ghi video khuôn mặt:</h3>
        <CameraRecorder
          onRecordingComplete={handleRecordingComplete}
          onError={handleError}
        />
      </div>

      {error && (
        <div style={{
          padding: '10px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          <strong>Lỗi:</strong> {error}
        </div>
      )}

      {uploadResult && (
        <div style={{
          padding: '10px',
          backgroundColor: '#d4edda',
          color: '#155724',
          border: '1px solid #c3e6cb',
          borderRadius: '4px',
          marginBottom: '20px',
          whiteSpace: 'pre-line'
        }}>
          <strong>Kết quả:</strong> {uploadResult}
        </div>
      )}

      <div style={{ textAlign: 'center' }}>
        <button
          onClick={handleSubmit}
          disabled={isUploading || !videoBlob || !employeeId.trim()}
          style={{
            padding: '12px 24px',
            fontSize: '16px',
            backgroundColor: isUploading ? '#6c757d' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isUploading ? 'not-allowed' : 'pointer',
            marginRight: '10px'
          }}
        >
          {isUploading ? 'Đang đăng ký...' : 'Đăng ký khuôn mặt'}
        </button>

        <button
          onClick={handleReset}
          disabled={isUploading}
          style={{
            padding: '12px 24px',
            fontSize: '16px',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isUploading ? 'not-allowed' : 'pointer'
          }}
        >
          Làm mới
        </button>
      </div>

      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
        <h4>Hướng dẫn:</h4>
        <ul style={{ textAlign: 'left' }}>
          <li>Nhập mã nhân viên</li>
          <li>Cho phép truy cập camera khi được yêu cầu</li>
          <li>Đặt khuôn mặt trong khung hình</li>
          <li>Nhấn "Bắt đầu ghi video" và quay khoảng 5-10 giây</li>
          <li>Nhấn "Dừng ghi video"</li>
          <li>Nhấn "Đăng ký khuôn mặt" để gửi lên server</li>
        </ul>
      </div>
    </div>
  );
};
