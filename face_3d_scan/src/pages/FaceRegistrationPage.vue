<template>
    <div class="registration-container">
        <h1>Face Registration</h1>

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
            <input
                v-model="employeeId"
                placeholder="Enter Employee ID"
                :disabled="isRecording"
                class="employee-input"
            />

            <button
                @click="startRegistration"
                :disabled="isRecording || !employeeId || !isFaceDetected"
                v-if="!recordingComplete"
                class="action-button"
            >
                Start Recording
            </button>

            <div v-if="recordingComplete" class="action-buttons">
                <button @click="retryRecording" class="action-button">
                    Retry
                </button>
                <button
                    @click="submitRegistration"
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
const employeeId = ref("");
const isRecording = ref(false);
const recordingComplete = ref(false);
const remainingTime = ref(10);
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

// Start recording process
async function startRegistration() {
    if (!employeeId.value) return;

    try {
        isRecording.value = true;
        remainingTime.value = 10;
        status.value = null;

        // Setup recording with 2x scale
        videoService.setupVideoProcessing({ scale: 2, duration: 10 });

        // Countdown timer
        const timer = setInterval(() => {
            remainingTime.value--;
        }, 1000);

        // Start recording
        recordedVideo.value = await videoService.startRecording({
            duration: 10,
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

// Submit registration
async function submitRegistration() {
    if (!recordedVideo.value || !employeeId.value) return;

    try {
        status.value = {
            message: "Uploading registration...",
            type: "success",
        };

        const response = await apiService.registerFace(
            recordedVideo.value,
            employeeId.value
        );

        status.value = {
            message: response.message,
            type: response.success ? "success" : "error",
        };

        if (response.success) {
            // Reset after successful registration
            setTimeout(() => {
                recordingComplete.value = false;
                recordedVideo.value = null;
                employeeId.value = "";
            }, 2000);
        }
    } catch (error) {
        status.value = {
            message: "Registration failed. Please try again.",
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
.registration-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
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

.employee-input {
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
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
