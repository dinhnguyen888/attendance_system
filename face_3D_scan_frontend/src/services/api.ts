import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface FaceRegistrationRequest {
  employeeId: string;
  videoBlob: Blob;
}

export interface AttendanceRequest {
  employeeId: string;
  videoBlob: Blob;
  type: 'checkin' | 'checkout';
}

class ApiService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
  });

  constructor() {
    this.api.interceptors.request.use(
      (config) => {
        console.log('API Request:', config.method?.toUpperCase(), config.url);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    this.api.interceptors.response.use(
      (response) => {
        console.log('API Response:', response.status, response.data);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.status, error.response?.data);
        return Promise.reject(error);
      }
    );
  }

  async registerFace(request: FaceRegistrationRequest): Promise<ApiResponse> {
    try {
      const formData = new FormData();
      formData.append('employee_id', request.employeeId);
      formData.append('video', request.videoBlob, 'face_scan.webm');

      console.log('Đang đăng ký khuôn mặt cho nhân viên:', request.employeeId);
      console.log('Kích thước video blob:', request.videoBlob.size, 'bytes');
      console.log('Loại video blob:', request.videoBlob.type);

      const response = await this.api.post('/api/3d-face-register', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return {
        success: true,
        data: response.data,
        message: 'Đăng ký khuôn mặt thành công',
      };
    } catch (error: any) {
      console.error('Lỗi đăng ký khuôn mặt:', error);
      console.error('Response lỗi:', error.response?.data);
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Đăng ký khuôn mặt thất bại',
      };
    }
  }

  async checkIn(request: AttendanceRequest): Promise<ApiResponse> {
    try {
      const formData = new FormData();
      formData.append('employee_id', request.employeeId);
      formData.append('video', request.videoBlob, 'checkin.webm');
      formData.append('type', request.type);

      const response = await this.api.post('/attendance/checkin', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return {
        success: true,
        data: response.data,
        message: 'Chấm công vào thành công',
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Chấm công vào thất bại',
      };
    }
  }

  async checkOut(request: AttendanceRequest): Promise<ApiResponse> {
    try {
      const formData = new FormData();
      formData.append('employee_id', request.employeeId);
      formData.append('video', request.videoBlob, 'checkout.webm');
      formData.append('type', request.type);

      const response = await this.api.post('/attendance/checkout', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return {
        success: true,
        data: response.data,
        message: 'Chấm công ra thành công',
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Chấm công ra thất bại',
      };
    }
  }

  async getEmployeeInfo(employeeId: string): Promise<ApiResponse<{ id: string; name?: string }>> {
    try {
      const response = await this.api.get(`/employee/${employeeId}`);
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Không thể lấy thông tin nhân viên',
      };
    }
  }
}

export const apiService = new ApiService();