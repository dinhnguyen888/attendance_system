export interface FaceDetectionResult {
  success: boolean;
  message: string;
  data?: {
    employeeId: string;
    confidence: number;
    timestamp: string;
  };
}

export interface RegistrationResult {
  success: boolean;
  message: string;
  employeeId?: string;
  faceCount?: number;
}

export interface VideoFrame {
  data: Uint8Array;
  width: number;
  height: number;
}

export type FaceRecognitionMode = 'register' | 'checkIn' | 'checkOut';

export interface FaceDetectionOptions {
  minConfidence?: number;
  maxFaces?: number;
  enable3D?: boolean;
}
