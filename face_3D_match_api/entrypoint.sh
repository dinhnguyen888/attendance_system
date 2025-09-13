#!/bin/sh
set -e

MODEL_DIR="/app/models"
MODEL_FILE="${MODEL_DIR}/resnet100.onnx"

mkdir -p "${MODEL_DIR}"

download_model() { :; }

is_valid_model() {
  # Basic validation: size > 5MB and not an HTML/LFS pointer
  if [ ! -f "${MODEL_FILE}" ]; then
    return 1
  fi
  size=$(stat -c%s "${MODEL_FILE}" 2>/dev/null || echo 0)
  if [ "$size" -lt 5000000 ]; then
    return 1
  fi
  if head -n 5 "${MODEL_FILE}" | grep -qiE "<html|git-lfs"; then
    return 1
  fi
  return 0
}

if [ ! -f "${MODEL_FILE}" ]; then
  echo "[entrypoint] ERROR: Missing model file ${MODEL_FILE}. Please mount or add it to the image." >&2
  exit 1
fi

echo "[entrypoint] ArcFace model found at ${MODEL_FILE}. Validating..."
if ! is_valid_model; then
  echo "[entrypoint] ERROR: Model file appears invalid (too small or not ONNX)." >&2
  exit 1
fi
echo "[entrypoint] Model looks valid."

# Normalize binary path for backward compatibility
if [ "$1" = "./build/face_3d_match_api" ] || [ "$1" = "build/face_3d_match_api" ]; then
  set -- "/app/face_3d_match_api" "${@:2}"
fi

# If the provided binary doesn't exist but the new one does, switch
if ! command -v "$1" >/dev/null 2>&1 && [ -x "/app/face_3d_match_api" ]; then
  set -- "/app/face_3d_match_api" "${@:2}"
fi

echo "[entrypoint] Starting: $@"
exec "$@"
