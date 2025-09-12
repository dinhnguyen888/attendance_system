interface FaceRecognitionResponse {
    success: boolean;
    message: string;
    match_score?: number;
    employee_id?: string;
    frames_processed?: number;
    error?: string;
}

export class ApiService {
    private readonly baseUrl: string;

    constructor() {
        this.baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8080";
    }

    private async sendVideoData(
        endpoint: string,
        videoBlob: Blob,
        metadata?: Record<string, any>
    ): Promise<FaceRecognitionResponse> {
        try {
            const formData = new FormData();
            // Changed from "video" to match the backend's expected field name
            formData.append("video_data", videoBlob, "face-recording.webm");

            if (metadata) {
                Object.entries(metadata).forEach(([key, value]) => {
                    formData.append(key, value.toString());
                });
            }

            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error("API call failed:", error);
            throw error;
        }
    }

    async registerFace(
        videoBlob: Blob,
        employeeId: string
    ): Promise<FaceRecognitionResponse> {
        const formData = new FormData();
        formData.append("video_data", videoBlob, "face-recording.webm");
        formData.append("employee_id", employeeId);

        try {
            const response = await fetch(`${this.baseUrl}/api/register`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Registration failed:", error);
            throw error;
        }
    }

    async verifyFace(videoBlob: Blob): Promise<FaceRecognitionResponse> {
        return this.sendVideoData("/api/verify", videoBlob);
    }

    async healthCheck(): Promise<boolean> {
        try {
            const response = await fetch(`${this.baseUrl}/api/health`);
            return response.ok;
        } catch {
            return false;
        }
    }
}

// Export singleton instance
export const apiService = new ApiService();
