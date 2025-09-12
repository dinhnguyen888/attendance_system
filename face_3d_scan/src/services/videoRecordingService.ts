interface VideoRecordingOptions {
    duration: number; // Duration in seconds
    scale: number; // Scale factor (2x = 2)
}

export class VideoRecordingService {
    private stream: MediaStream | null = null;
    private mediaRecorder: MediaRecorder | null = null;
    private chunks: Blob[] = [];
    private canvas: HTMLCanvasElement | null = null;
    private video: HTMLVideoElement | null = null;

    async initializeCamera(): Promise<void> {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                },
            });
        } catch (error) {
            throw new Error(`Failed to initialize camera: ${error}`);
        }
    }

    getStream(): MediaStream | null {
        return this.stream;
    }

    setupVideoProcessing(options: VideoRecordingOptions): void {
        if (!this.stream) throw new Error("Camera not initialized");

        // Create video element for input
        this.video = document.createElement("video");
        this.video.srcObject = this.stream;
        this.video.play();

        // Create canvas for processing
        this.canvas = document.createElement("canvas");
        const ctx = this.canvas.getContext("2d");
        if (!ctx) throw new Error("Failed to get canvas context");

        // Set canvas size with scale
        const baseWidth = 640; // Base width
        const baseHeight = 480; // Base height
        this.canvas.width = baseWidth * options.scale;
        this.canvas.height = baseHeight * options.scale;
    }

    startRecording(options: VideoRecordingOptions): Promise<Blob> {
        if (!this.stream || !this.canvas) {
            throw new Error("Recording not properly initialized");
        }

        const canvas = this.canvas; // Store reference to avoid null checks

        return new Promise((resolve, reject) => {
            const processFrame = () => {
                if (!this.video || !canvas) return;
                const ctx = canvas.getContext("2d");
                if (!ctx) return;

                // Calculate center crop
                const scale = options.scale;
                const srcWidth = this.video.videoWidth;
                const srcHeight = this.video.videoHeight;
                const cropWidth = srcWidth / scale;
                const cropHeight = srcHeight / scale;
                const srcX = (srcWidth - cropWidth) / 2;
                const srcY = (srcHeight - cropHeight) / 2;

                // Draw scaled and cropped frame
                ctx.drawImage(
                    this.video,
                    srcX,
                    srcY,
                    cropWidth,
                    cropHeight,
                    0,
                    0,
                    canvas.width,
                    canvas.height
                );
            };

            // Setup MediaRecorder with canvas stream
            const canvasStream = canvas.captureStream(30); // 30 FPS
            this.mediaRecorder = new MediaRecorder(canvasStream, {
                mimeType: "video/webm;codecs=vp9",
            });

            this.mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    this.chunks.push(e.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                const blob = new Blob(this.chunks, { type: "video/webm" });
                this.chunks = [];
                resolve(blob);
            };

            // Start processing frames
            const frameInterval = setInterval(processFrame, 1000 / 30);

            // Start recording
            this.mediaRecorder.start();

            // Stop after duration
            setTimeout(() => {
                clearInterval(frameInterval);
                this.mediaRecorder?.stop();
            }, options.duration * 1000);
        });
    }

    stopRecording(): void {
        this.mediaRecorder?.stop();
    }

    cleanup(): void {
        this.stream?.getTracks().forEach((track) => track.stop());
        this.stream = null;
        this.mediaRecorder = null;
        this.video = null;
        this.canvas = null;
        this.chunks = [];
    }
}
