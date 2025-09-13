import axios from 'axios';
import type { FaceRegistrationResponse, FaceRegistrationError } from '../types';

const API_BASE_URL = 'http://localhost:8080';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds for video upload
});

export const faceRegistrationApi = {
  async registerFace(employeeId: string, videoFile: File): Promise<FaceRegistrationResponse> {
    const formData = new FormData();
    formData.append('employee_id', employeeId);
    formData.append('video', videoFile);

    try {
      const response = await api.post<FaceRegistrationResponse>('/api/3d-face-register', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        const errorData = error.response.data as FaceRegistrationError;
        throw new Error(errorData.message || 'Registration failed');
      }
      throw new Error('Network error occurred');
    }
  },

  async checkHealth(): Promise<{ status: string }> {
    const response = await api.get('/api/health');
    return response.data;
  },
};
