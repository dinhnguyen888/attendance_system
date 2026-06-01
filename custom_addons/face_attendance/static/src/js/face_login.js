(function () {
    "use strict";

    function csrfToken() {
        const input = document.querySelector("input[name='csrf_token']");
        return input ? input.value : "";
    }

    function stopCamera(stream) {
        if (!stream) {
            return;
        }
        for (const track of stream.getTracks()) {
            track.stop();
        }
    }

    function recordVideo(stream, durationMs) {
        return new Promise((resolve, reject) => {
            const chunks = [];
            const mime = MediaRecorder.isTypeSupported("video/webm;codecs=vp8")
                ? "video/webm;codecs=vp8"
                : "video/webm";
            const recorder = new MediaRecorder(stream, { mimeType: mime });
            recorder.ondataavailable = (event) => {
                if (event.data && event.data.size) {
                    chunks.push(event.data);
                }
            };
            recorder.onerror = () => reject(recorder.error);
            recorder.onstop = () => resolve(new Blob(chunks, { type: recorder.mimeType || "video/webm" }));
            recorder.start();
            window.setTimeout(() => {
                if (recorder.state !== "inactive") {
                    recorder.stop();
                }
            }, durationMs);
        });
    }

    async function submitVideo(blob) {
        const formData = new FormData();
        formData.append("csrf_token", csrfToken());
        formData.append("face_video", blob, "face-login.webm");
        const response = await fetch("/resp_face_attendance/face_login/verify", {
            method: "POST",
            body: formData,
            credentials: "same-origin",
        });
        if (!response.ok) {
            throw new Error(`Face verification request failed with HTTP ${response.status}`);
        }
        return response.json();
    }

    async function openCamera(video) {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        video.srcObject = stream;
        await video.play();
        return stream;
    }

    async function startScan(modal) {
        const video = modal.querySelector(".o_resp_face_video");
        const status = modal.querySelector(".o_resp_face_status");
        const retry = modal.querySelector(".o_resp_face_retry");
        let stream = null;

        retry.classList.add("d-none");
        status.textContent = "Preparing camera...";
        modal.classList.remove("d-none");
        modal.setAttribute("aria-hidden", "false");

        try {
            try {
                stream = await openCamera(video);
            } catch (error) {
                console.error("Face login camera failed", error);
                status.textContent = "Unable to open camera. Check browser permission and HTTPS.";
                retry.classList.remove("d-none");
                return;
            }
            status.textContent = "Keep your face inside the frame...";

            const blob = await recordVideo(stream, 2500);
            status.textContent = "Verifying...";

            let result = null;
            try {
                result = await submitVideo(blob);
            } catch (error) {
                console.error("Face login verification request failed", error);
                status.textContent = "Unable to send verification video.";
                retry.classList.remove("d-none");
                return;
            }
            if (result.ok && result.redirect_url) {
                window.location.href = result.redirect_url;
                return;
            }
            status.textContent = result.message || "Unable to verify face.";
            retry.classList.remove("d-none");
        } catch (error) {
            status.textContent = "Unable to complete face verification.";
            retry.classList.remove("d-none");
            console.error("Face login failed", error);
        } finally {
            stopCamera(stream);
            video.srcObject = null;
        }
    }

    function closeScan(modal) {
        const video = modal.querySelector(".o_resp_face_video");
        stopCamera(video && video.srcObject);
        if (video) {
            video.srcObject = null;
        }
        modal.classList.add("d-none");
        modal.setAttribute("aria-hidden", "true");
    }

    document.addEventListener("click", (event) => {
        const modal = document.querySelector(".o_resp_face_modal");
        if (!modal) {
            return;
        }

        if (event.target.closest(".o_resp_face_login_btn")) {
            event.preventDefault();
            if (!navigator.mediaDevices || !window.MediaRecorder) {
                window.alert("This browser does not support face scan.");
                return;
            }
            startScan(modal);
            return;
        }

        if (event.target.closest(".o_resp_face_close, .o_resp_face_cancel")) {
            closeScan(modal);
            return;
        }

        if (event.target.closest(".o_resp_face_retry")) {
            startScan(modal);
        }
    });
}());
