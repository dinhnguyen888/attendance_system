"""Pure face inference workflows used by transport adapters."""
from collections import defaultdict
import logging
import os

import numpy as np

from app.inference.face import compare_embeddings, detect_faces, extract_embedding
from app.inference.media import decode_image, face_quality, portrait_photo_quality, sample_video_frames
from app.inference.spoofing import AntiSpoofingVerifier
from app.inference.status import (
    EMBEDDING_FAILED,
    ERROR,
    INTERNAL_ERROR,
    INVALID_PHOTO_ASPECT_RATIO,
    INVALID_PHOTO_BACKGROUND,
    INVALID_IMAGE,
    INVALID_VIDEO,
    MULTIPLE_FACES,
    NO_CANDIDATES,
    NO_FACE,
    OK,
    SPOOFING_DETECTED,
)

_logger = logging.getLogger(__name__)

MODEL_NAME = f"insightface/{os.getenv('INSIGHTFACE_MODEL', 'buffalo_l')}"


class FaceInferenceService:
    def __init__(self):
        self.anti_spoofing = AntiSpoofingVerifier()

    def register(self, image_bytes: bytes, request_id=None):
        try:
            _logger.info("AI inference register request: %s", {
                "request_id": request_id,
                "image_size_bytes": len(image_bytes or b""),
                "model_name": MODEL_NAME,
            })
            image = decode_image(image_bytes)
            if image is None:
                result = self._error(INVALID_IMAGE)
                _logger.info("AI inference register response: %s", {
                    "request_id": request_id,
                    **self._response_log_payload(result),
                })
                return result

            _logger.info("AI inference register decoded image: %s", {
                "request_id": request_id,
                "shape": tuple(int(value) for value in image.shape),
                "dtype": str(image.dtype),
            })

            faces, embedding = self._single_embedding(image)
            _logger.info("AI inference register detected faces: %s", {
                "request_id": request_id,
                "face_count": len(faces),
                "faces": [self._face_log_payload(face) for face in faces],
                "embedding": self._embedding_log_payload(embedding),
            })
            if len(faces) == 0:
                result = self._error(NO_FACE, face_count=0)
                _logger.info("AI inference register response: %s", {
                    "request_id": request_id,
                    **self._response_log_payload(result),
                })
                return result
            if len(faces) > 1:
                result = self._error(MULTIPLE_FACES, face_count=len(faces))
                _logger.info("AI inference register response: %s", {
                    "request_id": request_id,
                    **self._response_log_payload(result),
                })
                return result
            if embedding is None:
                result = self._error(EMBEDDING_FAILED, face_count=1, face_box=self._box(faces[0]))
                _logger.info("AI inference register response: %s", {
                    "request_id": request_id,
                    **self._response_log_payload(result),
                })
                return result

            photo_quality = portrait_photo_quality(image, faces[0])
            _logger.info("AI inference register portrait photo quality: %s", {
                "request_id": request_id,
                **photo_quality,
            })
            if not photo_quality["aspect_ratio_ok"]:
                result = self._error(INVALID_PHOTO_ASPECT_RATIO, face_count=1, face_box=self._box(faces[0]), **photo_quality)
                _logger.info("AI inference register response: %s", {
                    "request_id": request_id,
                    **self._response_log_payload(result),
                })
                return result
            if not photo_quality["background_ok"]:
                result = self._error(INVALID_PHOTO_BACKGROUND, face_count=1, face_box=self._box(faces[0]), **photo_quality)
                _logger.info("AI inference register response: %s", {
                    "request_id": request_id,
                    **self._response_log_payload(result),
                })
                return result

            embedding = np.asarray(embedding, dtype=np.float32)
            result = {
                "status": OK,
                "message": OK,
                "embedding": embedding.tolist(),
                "embedding_dim": int(embedding.shape[0]),
                "model_name": MODEL_NAME,
                "face_count": 1,
                "face_box": self._box(faces[0]),
                **face_quality(image, faces[0]),
                **photo_quality,
            }
            _logger.info("AI inference register response: %s", {
                "request_id": request_id,
                **self._response_log_payload(result),
            })
            return result
        except Exception:
            _logger.exception("AI inference register failed: request_id=%s", request_id)
            return self._error(INTERNAL_ERROR)

    def analyze(self, video_bytes: bytes, candidates, max_frames: int = 7, request_id=None):
        try:
            _logger.info("AI inference analyze request: %s", {
                "request_id": request_id,
                "video_size_bytes": len(video_bytes or b""),
                "max_frames": int(max_frames or 7),
                "candidate_count": len(candidates or []),
                "candidates": [self._candidate_log_payload(candidate) for candidate in (candidates or [])],
            })
            if not video_bytes:
                result = self._error(INVALID_VIDEO)
                _logger.info("AI inference analyze response: %s", {
                    "request_id": request_id,
                    **self._response_log_payload(result),
                })
                return result
            candidates = [candidate for candidate in candidates if candidate.get("registered_embedding")]
            if not candidates:
                result = self._error(NO_CANDIDATES)
                _logger.info("AI inference analyze response: %s", {
                    "request_id": request_id,
                    **self._response_log_payload(result),
                })
                return result

            frames = sample_video_frames(video_bytes, max_frames)
            if not frames:
                result = self._error(INVALID_VIDEO)
                _logger.info("AI inference analyze response: %s", {
                    "request_id": request_id,
                    **self._response_log_payload(result),
                })
                return result

            _logger.info("AI inference analyze sampled frames: %s", {
                "request_id": request_id,
                "frame_count": len(frames),
                "frames": [
                    {
                        "frame_index": int(frame_index),
                        "shape": tuple(int(value) for value in frame.shape),
                        "dtype": str(frame.dtype),
                    }
                    for frame_index, frame in frames
                ],
            })

            scores = defaultdict(list)
            frame_results = []
            spoofed_count = 0
            best = {"similarity": -1.0, "frame_index": -1, "candidate": None}

            for frame_index, frame in frames:
                frame_result, best = self._analyze_frame(frame_index, frame, candidates, scores, best, request_id=request_id)
                spoofed_count += int(frame_result["spoofing_detected"])
                frame_results.append(frame_result)

            candidate_results, all_scores = self._candidate_results(candidates, scores)
            result = {
                "status": OK,
                "message": OK,
                "processed_frame_count": len(frames),
                "valid_frame_count": sum(1 for frame in frame_results if frame["valid"]),
                "spoofed_frame_count": spoofed_count,
                "spoofing_error_rate": float(spoofed_count / len(frames)),
                "best_candidate_user_id": int(best["candidate"]["user_id"]) if best["candidate"] else 0,
                "best_candidate_employee_id": int(best["candidate"]["employee_id"]) if best["candidate"] else 0,
                "max_similarity": float(max(all_scores)) if all_scores else 0.0,
                "avg_similarity": float(np.mean(all_scores)) if all_scores else 0.0,
                "min_similarity": float(min(all_scores)) if all_scores else 0.0,
                "best_frame_index": best["frame_index"],
                "candidates": candidate_results,
                "frames": frame_results,
            }
            _logger.info("AI inference analyze response: %s", {
                "request_id": request_id,
                **self._response_log_payload(result),
            })
            return result
        except Exception:
            _logger.exception("AI inference analyze failed: request_id=%s", request_id)
            return self._error(INTERNAL_ERROR)

    def _analyze_frame(self, frame_index, frame, candidates, scores, best, request_id=None):
        spoofing_detected = bool(self.anti_spoofing.verify_no_device_spoofing(frame).get("spoofing_detected"))
        faces, embedding = self._single_embedding(frame)
        error_code = self._frame_error(len(faces), spoofing_detected, embedding)
        result = {
            "frame_index": int(frame_index),
            "valid": not bool(error_code),
            "face_count": len(faces),
            "spoofing_detected": spoofing_detected,
            "error_code": error_code,
            "similarity_by_candidate": [],
        }
        _logger.info("AI inference analyze frame detection: %s", {
            "request_id": request_id,
            "frame_index": int(frame_index),
            "shape": tuple(int(value) for value in frame.shape),
            "face_count": len(faces),
            "faces": [self._face_log_payload(face) for face in faces],
            "spoofing_detected": spoofing_detected,
            "embedding": self._embedding_log_payload(embedding),
            "error_code": error_code,
        })
        if error_code:
            return result, best

        current_embedding = np.asarray(embedding, dtype=np.float32)
        for candidate in candidates:
            key = self._candidate_key(candidate)
            similarity = float(compare_embeddings(current_embedding, np.asarray(candidate["registered_embedding"], dtype=np.float32)))
            scores[key].append(similarity)
            result["similarity_by_candidate"].append({
                "user_id": int(candidate["user_id"]),
                "employee_id": int(candidate["employee_id"]),
                "similarity": similarity,
            })
            if similarity > best["similarity"]:
                best = {"similarity": similarity, "frame_index": int(frame_index), "candidate": candidate}
        _logger.info("AI inference analyze frame similarities: %s", {
            "request_id": request_id,
            "frame_index": int(frame_index),
            "similarity_by_candidate": result["similarity_by_candidate"],
            "best_similarity": best["similarity"],
            "best_candidate": self._candidate_log_payload(best["candidate"]) if best["candidate"] else None,
        })
        return result, best

    def _candidate_results(self, candidates, scores):
        results = []
        all_scores = []
        for candidate in candidates:
            values = scores.get(self._candidate_key(candidate), [])
            all_scores.extend(values)
            max_similarity = max(values) if values else 0.0
            results.append({
                "user_id": int(candidate["user_id"]),
                "employee_id": int(candidate["employee_id"]),
                "threshold": float(candidate["threshold"]),
                "max_similarity": float(max_similarity),
                "avg_similarity": float(np.mean(values)) if values else 0.0,
                "min_similarity": float(min(values)) if values else 0.0,
                "similarity_margin": float(max_similarity - float(candidate["threshold"])),
            })
        return results, all_scores

    @staticmethod
    def _single_embedding(image):
        faces = detect_faces(image)
        return faces, extract_embedding(image, faces[0]) if len(faces) == 1 else None

    @staticmethod
    def _frame_error(face_count, spoofing_detected, embedding):
        if spoofing_detected:
            return SPOOFING_DETECTED
        if face_count == 0:
            return NO_FACE
        if face_count > 1:
            return MULTIPLE_FACES
        if embedding is None:
            return EMBEDDING_FAILED
        return ""

    @staticmethod
    def _candidate_key(candidate):
        return int(candidate["user_id"]), int(candidate["employee_id"])

    @staticmethod
    def _box(face_info):
        x, y, w, h = face_info[:4]
        return {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}

    @staticmethod
    def _error(code, **extra):
        return {"status": ERROR, "error_code": code, "message": code, **extra}

    @staticmethod
    def _embedding_log_payload(values):
        if values is None:
            return {"present": False, "length": 0}
        values = np.asarray(values, dtype=np.float32)
        if values.size == 0:
            return {"present": True, "length": 0}
        return {
            "present": True,
            "length": int(values.size),
            "min": float(values.min()),
            "max": float(values.max()),
            "mean": float(values.mean()),
            "first_values": [float(value) for value in values[:5]],
        }

    @classmethod
    def _candidate_log_payload(cls, candidate):
        if not candidate:
            return None
        return {
            "user_id": int(candidate["user_id"]),
            "employee_id": int(candidate["employee_id"]),
            "threshold": float(candidate["threshold"]),
            "registered_embedding": cls._embedding_log_payload(candidate.get("registered_embedding")),
        }

    @classmethod
    def _face_log_payload(cls, face_info):
        payload = {"box": cls._box(face_info)}
        face = face_info[4] if len(face_info) > 4 else None
        if face is not None:
            if getattr(face, "det_score", None) is not None:
                payload["det_score"] = float(face.det_score)
            if getattr(face, "kps", None) is not None:
                payload["landmark_count"] = int(len(face.kps))
        return payload

    @classmethod
    def _response_log_payload(cls, result):
        payload = dict(result)
        if "embedding" in payload:
            payload["embedding"] = cls._embedding_log_payload(payload["embedding"])
        if "candidates" in payload:
            payload["candidates"] = list(payload["candidates"])
        if "frames" in payload:
            payload["frames"] = list(payload["frames"])
        return payload
