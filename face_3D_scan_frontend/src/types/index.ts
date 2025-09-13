export interface Employee {
  id: string;
  name?: string;
}

export interface FaceScanResult {
  success: boolean;
  message: string;
  videoBlob?: Blob;
}

export interface ScanProgress {
  isScanning: boolean;
  progress: number;
  phase: 'waiting' | 'face_detection' | 'circle_scan' | 'complete';
}

export interface FaceMeshDetection {
  isDetected: boolean;
  landmarks?: any[];
  confidence?: number;
}