export interface FaceRegistrationResponse {
  message: string;
  video: string;
  frames_dir: string;
  preprocess_dir: string;
  embedding_dir: string;
}

export interface FaceRegistrationError {
  message: string;
}

export interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  blob: Blob | null;
}
