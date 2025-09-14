import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  similarity?: number;
  match?: boolean;
  action?: string;
}

export interface FaceRegistrationRequest {
  employeeId: string;
  videoBlob: Blob;
}

export interface AttendanceRequest {
  employeeId: string;
  videoBlob: Blob;
  type: 'checkin' | 'checkout';
  wifiIp?: string;
}

class ApiService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
  });

  // Function to get WiFi IP address
  private async getWifiIp(): Promise<string> {
    try {
      // Try to get IP from a public service first
      const response = await fetch('https://api.ipify.org?format=json');
      const data = await response.json();
      return data.ip || 'UNKNOWN_WIFI';
    } catch (error) {
      console.warn('Could not get public IP, trying local hostname:', error);
      try {
        // Fallback to local hostname/IP
        return window.location.hostname || 'UNKNOWN_WIFI';
      } catch (localError) {
        console.warn('Could not get local IP:', localError);
        return 'UNKNOWN_WIFI';
      }
    }
  }

  // Helper function to convert base64 to Blob
  private base64ToBlob(base64Data: string, contentType: string = 'image/jpeg'): Blob {
    // Remove data URL prefix if present
    const base64 = base64Data.replace(/^data:image\/[a-z]+;base64,/, '');
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: contentType });
  }

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
      console.log('🚀 Starting unified check-in flow...');
      
      // Step 1: Call face_3D_match_api (server.cpp) first
      console.log('📡 Step 1: Calling face recognition API...');
      const faceFormData = new FormData();
      faceFormData.append('employee_id', request.employeeId);
      faceFormData.append('video', request.videoBlob, 'checkin.webm');

      const faceResponse = await this.api.post('/api/checkin', faceFormData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        validateStatus: function (status: number) {
          // Accept both 200 (success) and 401 (verification failed) as valid responses
          return status === 200 || status === 401;
        }
      });

      // Check for 401 status code - authentication/verification failed
      if (faceResponse.status === 401) {
        console.error('❌ Face verification failed (401):', faceResponse.data);
        return {
          success: false,
          error: faceResponse.data?.message || 'Xác thực khuôn mặt thất bại - không được phép chấm công',
          similarity: faceResponse.data?.similarity,
          match: false
        };
      }

      if (!faceResponse.data) {
        throw new Error('Face recognition failed - no data returned');
      }

      console.log('✅ Face recognition completed:', faceResponse.data);
      console.log('🔍 Similarity value:', faceResponse.data.similarity);
      console.log('🔍 Available fields:', Object.keys(faceResponse.data));
      
      // Step 2: Get WiFi IP
      const wifiIp = request.wifiIp || await this.getWifiIp();
      console.log('📍 WiFi IP detected:', wifiIp);
      
      // Step 3: Call controller.py with face recognition results
      console.log('💾 Step 2: Calling database controller...');
      console.log('🔗 Controller URL: http://localhost:8069/3d-scan/check-in');
      console.log('📊 Data being sent:', {
        employee_id: request.employeeId,
        confidence: faceResponse.data.similarity?.toString() || '0',
        verification_message: faceResponse.data.message || 'Face recognition check-in',
        wifi_ip: wifiIp,
        has_comparison_image: !!faceResponse.data.comparison_image
      });
      
      const controllerFormData = new FormData();
      controllerFormData.append('employee_id', request.employeeId);
      controllerFormData.append('confidence', faceResponse.data.similarity?.toString() || '0');
      controllerFormData.append('verification_message', faceResponse.data.message || 'Face recognition check-in');
      controllerFormData.append('wifi_ip', wifiIp);
      
      // Convert base64 image to blob and add as files
      if (faceResponse.data.comparison_image) {
        const comparisonBlob = this.base64ToBlob(faceResponse.data.comparison_image);
        // Only send check_in_image to controller
        controllerFormData.append('check_in_image', comparisonBlob, 'checkin_image.jpg');
        console.log('📸 Check-in image attached to form data');
      } else {
        console.warn('⚠️ No comparison_image received from face recognition API');
      }

      try {
        // Call Odoo controller
        console.log('🚀 Making request to controller...');
        const controllerResponse = await fetch('http://localhost:8069/3d-scan/check-in', {
          method: 'POST',
          body: controllerFormData
        });

        console.log('📡 Controller response status:', controllerResponse.status);
        console.log('📡 Controller response headers:', Object.fromEntries(controllerResponse.headers.entries()));

        if (!controllerResponse.ok) {
          const errorText = await controllerResponse.text();
          console.error('❌ Controller error response:', errorText);
          try {
            const errorData = JSON.parse(errorText);
            throw new Error(errorData.message || `Database update failed (${controllerResponse.status})`);
          } catch (parseError) {
            throw new Error(`Database update failed (${controllerResponse.status})`);
          }
        }
        const controllerResult = await controllerResponse.json();
        console.log('✅ Database update completed:', controllerResult);
        
        // Return combined result with face recognition fields at top level
        return {
          success: true,
          data: {
            ...controllerResult,
            face_recognition: faceResponse.data,
            wifi_ip: wifiIp
          },
          message: 'Chấm công vào thành công',
          // Add face recognition fields at top level for App.tsx compatibility
          similarity: faceResponse.data.similarity,
          match: faceResponse.data.match,
          action: 'checkin'
        };
      } catch (fetchError: any) {
        console.error('❌ Network error calling controller:', fetchError);
        throw new Error(`Failed to connect to database controller: ${fetchError.message}`);
      }
    } catch (error: any) {
      console.error('❌ Check-in flow failed:', error);
      return {
        success: false,
        error: error.message || 'Chấm công vào thất bại',
      };
    }
  }

  async checkOut(request: AttendanceRequest): Promise<ApiResponse> {
    try {
      console.log('🚀 Starting unified check-out flow...');
      
      // Step 1: Call face_3D_match_api (server.cpp) first
      console.log('📡 Step 1: Calling face recognition API...');
      const faceFormData = new FormData();
      faceFormData.append('employee_id', request.employeeId);
      faceFormData.append('video', request.videoBlob, 'checkout.webm');

      const faceResponse = await this.api.post('/api/checkout', faceFormData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        validateStatus: function (status: number) {
          // Accept both 200 (success) and 401 (verification failed) as valid responses
          return status === 200 || status === 401;
        }
      });

      // Check for 401 status code - authentication/verification failed
      if (faceResponse.status === 401) {
        console.error('❌ Face verification failed (401):', faceResponse.data);
        return {
          success: false,
          error: faceResponse.data?.message || 'Xác thực khuôn mặt thất bại - không được phép chấm công',
          similarity: faceResponse.data?.similarity,
          match: false
        };
      }

      if (!faceResponse.data) {
        throw new Error('Face recognition failed - no data returned');
      }

      console.log('✅ Face recognition completed:', faceResponse.data);
      
      // Step 2: Get WiFi IP
      const wifiIp = request.wifiIp || await this.getWifiIp();
      console.log('📍 WiFi IP detected:', wifiIp);
      
      // Step 3: Call controller.py with face recognition results
      console.log('💾 Step 2: Calling database controller...');
      const controllerFormData = new FormData();
      controllerFormData.append('employee_id', request.employeeId);
      controllerFormData.append('confidence', faceResponse.data.similarity?.toString() || '0');
      controllerFormData.append('verification_message', faceResponse.data.message || 'Face recognition check-out');
      controllerFormData.append('wifi_ip', wifiIp);
      
      // Convert base64 image to blob and add as files
      if (faceResponse.data.comparison_image) {
        const comparisonBlob = this.base64ToBlob(faceResponse.data.comparison_image);
        // Only send check_out_image to controller
        controllerFormData.append('check_out_image', comparisonBlob, 'checkout_image.jpg');
        console.log('📸 Check-out image attached to form data');
      } else {
        console.warn('⚠️ No comparison_image received from face recognition API');
      }

      // Call Odoo controller
      const controllerResponse = await fetch('http://localhost:8069/3d-scan/check-out', {
        method: 'POST',
        body: controllerFormData
      });

      if (!controllerResponse.ok) {
        const errorText = await controllerResponse.text();
        console.error('❌ Controller error response:', errorText);
        try {
          const errorData = JSON.parse(errorText);
          throw new Error(errorData.message || `Database update failed (${controllerResponse.status})`);
        } catch (parseError) {
          throw new Error(`Database update failed (${controllerResponse.status})`);
        }
      }

      const controllerResult = await controllerResponse.json();
      console.log('✅ Database update completed:', controllerResult);

      // Return combined result with face recognition fields at top level
      return {
        success: true,
        data: {
          ...controllerResult,
          face_recognition: faceResponse.data,
          wifi_ip: wifiIp
        },
        message: 'Chấm công ra thành công',
        // Add face recognition fields at top level for App.tsx compatibility
        similarity: faceResponse.data.similarity,
        match: faceResponse.data.match,
        action: 'checkout'
      };
    } catch (error: any) {
      console.error('❌ Check-out flow failed:', error);
      return {
        success: false,
        error: error.message || 'Chấm công ra thất bại',
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