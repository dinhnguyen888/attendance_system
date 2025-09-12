import { FaceMesh, FACEMESH_TESSELATION, Results } from "@mediapipe/face_mesh";

export class FaceMeshService {
    private faceMesh: FaceMesh;
    private isInitialized = false;
    private canvas: HTMLCanvasElement | null = null;
    private ctx: CanvasRenderingContext2D | null = null;

    constructor() {
        this.faceMesh = new FaceMesh({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
            },
        });

        this.faceMesh.setOptions({
            maxNumFaces: 1,
            refineLandmarks: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5,
        });
    }

    async initialize(
        videoElement: HTMLVideoElement,
        overlayCanvas: HTMLCanvasElement
    ): Promise<void> {
        if (this.isInitialized) return;

        this.canvas = overlayCanvas;
        this.ctx = this.canvas.getContext("2d");

        if (!this.ctx) {
            throw new Error("Could not get canvas context");
        }

        await this.faceMesh.initialize();

        this.faceMesh.onResults((results) => {
            this.drawMesh(results);
        });

        this.isInitialized = true;
    }

    async processFaceMesh(videoElement: HTMLVideoElement): Promise<void> {
        if (!this.isInitialized) {
            throw new Error("FaceMesh not initialized");
        }

        await this.faceMesh.send({ image: videoElement });
    }

    private drawMesh(results: Results): void {
        if (!this.ctx || !this.canvas) return;

        const ctx = this.ctx;
        const canvas = this.canvas;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (results.multiFaceLandmarks) {
            for (const landmarks of results.multiFaceLandmarks) {
                // Draw face mesh tesselation
                ctx.strokeStyle = "rgba(66, 153, 225, 0.5)";
                ctx.lineWidth = 1;

                FACEMESH_TESSELATION.forEach(([i, j]) => {
                    const start = landmarks[i];
                    const end = landmarks[j];

                    if (start && end) {
                        ctx.beginPath();
                        ctx.moveTo(
                            start.x * canvas.width,
                            start.y * canvas.height
                        );
                        ctx.lineTo(end.x * canvas.width, end.y * canvas.height);
                        ctx.stroke();
                    }
                });

                // Draw contour points
                ctx.fillStyle = "rgba(66, 153, 225, 0.7)";
                landmarks.forEach((point) => {
                    ctx.beginPath();
                    ctx.arc(
                        point.x * canvas.width,
                        point.y * canvas.height,
                        1,
                        0,
                        2 * Math.PI
                    );
                    ctx.fill();
                });
            }
        }
    }

    cleanup(): void {
        this.faceMesh.close();
        this.isInitialized = false;
        this.canvas = null;
        this.ctx = null;
    }
}

// Export singleton instance
export const faceMeshService = new FaceMeshService();
