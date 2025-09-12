<template>
    <div class="verification-container">
        <h1>Face Verification</h1>

        <div class="verification-type">
            <button
                v-for="type in ['check-in', 'check-out']"
                :key="type"
                :class="['type-button', { active: verificationType === type }]"
                @click="verificationType = type"
                :disabled="isRecording"
            >
                {{ type.charAt(0).toUpperCase() + type.slice(1) }}
            </button>
        </div>

        <div class="video-container">
            <!-- Video preview with mesh overlay -->
            <div
                class="video-preview"
                v-if="!isRecording && !recordingComplete"
            >
                <video ref="previewVideo" autoplay playsinline></video>
                <canvas ref="meshCanvas" class="mesh-overlay"></canvas>
                <div class="overlay-guide">
                    <div class="face-guide"></div>
                </div>
            </div>

            <!-- Recording countdown -->
            <div class="countdown" v-if="isRecording">
                Recording: {{ remainingTime }}s
            </div>

            <!-- Preview recorded video -->
            <div class="recording-preview" v-if="recordingComplete">
                <video ref="recordingPreview" controls playsinline></video>
            </div>
        </div>

        <!-- Controls -->
        <div class="controls">
            <button
                @click="startVerification"
                :disabled="isRecording || !isFaceDetected"
                v-if="!recordingComplete"
                class="action-button"
            >
                Start {{ verificationType }}
            </button>

            <div v-if="recordingComplete" class="action-buttons">
                <button @click="retryRecording" class="action-button">
                    Retry
                </button>
                <button
                    @click="submitVerification"
                    class="action-button primary"
                >
                    Submit
                </button>
            </div>
        </div>

        <!-- Status messages -->
        <div v-if="status" :class="['status-message', status.type]">
            {{ status.message }}
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import {
    VideoRecordingService,
    faceMeshService,
    apiService,
} from "../services";

// State
const verificationType = ref<"check-in" | "check-out">("check-in");
const isRecording = ref(false);
const recordingComplete = ref(false);
const remainingTime = ref(3);
const recordedVideo = ref<Blob | null>(null);
const status = ref<{ message: string; type: "error" | "success" } | null>(null);
const isFaceDetected = ref(false);

// Refs
const previewVideo = ref<HTMLVideoElement | null>(null);
const recordingPreview = ref<HTMLVideoElement | null>(null);
const meshCanvas = ref<HTMLCanvasElement | null>(null);

// Services
const videoService = new VideoRecordingService();

let faceMeshInterval: number | null = null;

// Initialize camera and face mesh
onMounted(async () => {
    try {
        await videoService.initializeCamera();
        if (previewVideo.value && meshCanvas.value) {
            previewVideo.value.srcObject = videoService.getStream();

            // Initialize face mesh
            await faceMeshService.initialize(
                previewVideo.value,
                meshCanvas.value
            );

            // Start face mesh processing
            faceMeshInterval = window.setInterval(async () => {
                if (
                    previewVideo.value &&
                    !isRecording.value &&
                    !recordingComplete.value
                ) {
                    await faceMeshService.processFaceMesh(previewVideo.value);
                    isFaceDetected.value = true;
                }
            }, 100);
        }
    } catch (error) {
        status.value = {
            message: "Failed to initialize camera. Please check permissions.",
            type: "error",
        };
    }
});

// Cleanup
onUnmounted(() => {
    if (faceMeshInterval) {
        clearInterval(faceMeshInterval);
    }
    videoService.cleanup();
    faceMeshService.cleanup();
});

// Start verification process
async function startVerification() {
    try {
        isRecording.value = true;
        remainingTime.value = 3;
        status.value = null;

        // Setup recording with 2x scale
        videoService.setupVideoProcessing({ scale: 2, duration: 3 });

        // Countdown timer
        const timer = setInterval(() => {
            remainingTime.value--;
        }, 1000);

        // Start recording
        recordedVideo.value = await videoService.startRecording({
            duration: 3,
            scale: 2,
        });

        clearInterval(timer);
        isRecording.value = false;
        recordingComplete.value = true;

        // Show recording preview
        if (recordingPreview.value && recordedVideo.value) {
            recordingPreview.value.src = URL.createObjectURL(
                recordedVideo.value
            );
        }
    } catch (error) {
        status.value = {
            message: "Recording failed. Please try again.",
            type: "error",
        };
        isRecording.value = false;
    }
}

// Submit verification
async function submitVerification() {
    if (!recordedVideo.value) return;

    try {
        status.value = {
            message: "Verifying...",
            type: "success",
        };

        const response = await apiService.verifyFace(recordedVideo.value);

        if (response.success) {
            status.value = {
                message: `${
                    verificationType.value.charAt(0).toUpperCase() +
                    verificationType.value.slice(1)
                } successful!`,
                type: "success",
            };

            // Reset after successful verification
            setTimeout(() => {
                recordingComplete.value = false;
                recordedVideo.value = null;
            }, 2000);
        } else {
            status.value = {
                message: response.message || "Verification failed",
                type: "error",
            };
        }
    } catch (error) {
        status.value = {
            message: "Verification failed. Please try again.",
            type: "error",
        };
    }
}

// Retry recording
function retryRecording() {
    recordingComplete.value = false;
    recordedVideo.value = null;
    status.value = null;
}
</script>

<style scoped>
.verification-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

.verification-type {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-bottom: 20px;
}

.type-button {
    padding: 10px 20px;
    font-size: 16px;
    border: 1px solid #4299e1;
    background: transparent;
    color: #4299e1;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.type-button.active {
    background: #4299e1;
    color: white;
}

.type-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.video-container {
    position: relative;
    width: 100%;
    aspect-ratio: 16/9;
    background: #000;
    margin: 20px 0;
    border-radius: 8px;
    overflow: hidden;
}

.video-preview {
    position: relative;
    width: 100%;
    height: 100%;
}

.mesh-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}

video {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.overlay-guide {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    pointer-events: none;
}

.face-guide {
    width: 200px;
    height: 200px;
    border: 2px solid rgba(255, 255, 255, 0.5);
    border-radius: 50%;
}

.countdown {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 24px;
    color: white;
    background: rgba(0, 0, 0, 0.7);
    padding: 10px 20px;
    border-radius: 4px;
}

.controls {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 20px;
}

.action-buttons {
    display: flex;
    gap: 10px;
    justify-content: center;
}

.action-button {
    padding: 10px 20px;
    font-size: 16px;
    border: none;
    border-radius: 4px;
    background: #4a5568;
    color: white;
    cursor: pointer;
    transition: background 0.2s;
}

.action-button:disabled {
    background: #cbd5e0;
    cursor: not-allowed;
}

.action-button.primary {
    background: #4299e1;
}

.action-button:hover:not(:disabled) {
    opacity: 0.9;
}

.status-message {
    margin-top: 20px;
    padding: 10px;
    border-radius: 4px;
    text-align: center;
}

.status-message.error {
    background: #fed7d7;
    color: #c53030;
}

.status-message.success {
    background: #c6f6d5;
    color: #2f855a;
}
</style>
