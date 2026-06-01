"""gRPC adapter for the face inference service."""
from concurrent import futures
import logging
import time
import uuid

import grpc

from app.grpc.generated import face_recognition_pb2 as pb2
from app.grpc.generated import face_recognition_pb2_grpc as pb2_grpc
from app.inference.service import FaceInferenceService

_logger = logging.getLogger(__name__)


def _context_metadata(context):
    return {key: value for key, value in context.invocation_metadata()}


def _embedding_summary(values):
    if not values:
        return {"length": 0}
    return {
        "length": len(values),
        "min": min(values),
        "max": max(values),
        "first_values": list(values[:5]),
    }


def _face_box_payload(face_box):
    return {
        "x": face_box.x,
        "y": face_box.y,
        "width": face_box.width,
        "height": face_box.height,
    }


class FaceRecognitionGrpcService(pb2_grpc.FaceRecognitionServicer):
    def __init__(self):
        self.inference = FaceInferenceService()

    def RegisterFace(self, request, context):
        request_id = uuid.uuid4().hex
        started_at = time.perf_counter()
        _logger.info("AI gRPC RegisterFace request: %s", {
            "request_id": request_id,
            "peer": context.peer(),
            "metadata": _context_metadata(context),
            "employee_id": request.employee_id,
            "image_mime": request.image_mime,
            "image_size_bytes": len(request.image_bytes or b""),
        })
        result = self.inference.register(request.image_bytes, request_id=request_id)
        response = pb2.RegisterFaceResponse(
            status=result.get("status", ""),
            error_code=result.get("error_code", ""),
            message=result.get("message", ""),
            embedding=result.get("embedding", []),
            embedding_dim=result.get("embedding_dim", 0),
            model_name=result.get("model_name", ""),
            face_count=result.get("face_count", 0),
            blur_score=result.get("blur_score", 0.0),
            brightness_score=result.get("brightness_score", 0.0),
        )
        if result.get("face_box"):
            response.face_box.CopyFrom(pb2.FaceBox(**result["face_box"]))
        _logger.info("AI gRPC RegisterFace response: %s", {
            "request_id": request_id,
            "peer": context.peer(),
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "employee_id": request.employee_id,
            "status": response.status,
            "error_code": response.error_code,
            "message": response.message,
            "embedding_dim": response.embedding_dim,
            "embedding": _embedding_summary(response.embedding),
            "model_name": response.model_name,
            "face_count": response.face_count,
            "face_box": _face_box_payload(response.face_box) if response.HasField("face_box") else None,
            "blur_score": response.blur_score,
            "brightness_score": response.brightness_score,
        })
        return response

    def AnalyzeFace(self, request, context):
        request_id = uuid.uuid4().hex
        started_at = time.perf_counter()
        _logger.info("AI gRPC AnalyzeFace request: %s", {
            "request_id": request_id,
            "peer": context.peer(),
            "metadata": _context_metadata(context),
            "video_mime": request.video_mime,
            "video_size_bytes": len(request.video_bytes or b""),
            "max_frames": request.max_frames,
            "candidate_count": len(request.candidates),
            "candidates": [
                {
                    "user_id": item.user_id,
                    "employee_id": item.employee_id,
                    "threshold": item.threshold,
                    "embedding": _embedding_summary(item.registered_embedding),
                }
                for item in request.candidates
            ],
        })
        candidates = [
            {
                "user_id": item.user_id,
                "employee_id": item.employee_id,
                "registered_embedding": item.registered_embedding,
                "threshold": item.threshold,
            }
            for item in request.candidates
        ]
        result = self.inference.analyze(request.video_bytes, candidates, request.max_frames, request_id=request_id)
        response = pb2.AnalyzeFaceResponse(
            status=result.get("status", ""),
            error_code=result.get("error_code", ""),
            message=result.get("message", ""),
            processed_frame_count=result.get("processed_frame_count", 0),
            valid_frame_count=result.get("valid_frame_count", 0),
            spoofed_frame_count=result.get("spoofed_frame_count", 0),
            spoofing_error_rate=result.get("spoofing_error_rate", 0.0),
            best_candidate_user_id=result.get("best_candidate_user_id", 0),
            best_candidate_employee_id=result.get("best_candidate_employee_id", 0),
            max_similarity=result.get("max_similarity", 0.0),
            avg_similarity=result.get("avg_similarity", 0.0),
            min_similarity=result.get("min_similarity", 0.0),
            best_frame_index=result.get("best_frame_index", -1),
        )
        response.candidates.extend(pb2.CandidateMetrics(**item) for item in result.get("candidates", []))
        for item in result.get("frames", []):
            item = dict(item)
            similarities = item.pop("similarity_by_candidate", [])
            frame = pb2.FrameMetrics(**item)
            frame.similarity_by_candidate.extend(pb2.CandidateSimilarity(**similarity) for similarity in similarities)
            response.frames.append(frame)
        _logger.info("AI gRPC AnalyzeFace response: %s", {
            "request_id": request_id,
            "peer": context.peer(),
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "status": response.status,
            "error_code": response.error_code,
            "message": response.message,
            "processed_frame_count": response.processed_frame_count,
            "valid_frame_count": response.valid_frame_count,
            "spoofed_frame_count": response.spoofed_frame_count,
            "spoofing_error_rate": response.spoofing_error_rate,
            "best_candidate_user_id": response.best_candidate_user_id,
            "best_candidate_employee_id": response.best_candidate_employee_id,
            "max_similarity": response.max_similarity,
            "avg_similarity": response.avg_similarity,
            "min_similarity": response.min_similarity,
            "best_frame_index": response.best_frame_index,
            "candidate_metrics": [
                {
                    "user_id": item.user_id,
                    "employee_id": item.employee_id,
                    "threshold": item.threshold,
                    "max_similarity": item.max_similarity,
                    "avg_similarity": item.avg_similarity,
                    "min_similarity": item.min_similarity,
                    "similarity_margin": item.similarity_margin,
                }
                for item in response.candidates
            ],
            "frame_metrics": [
                {
                    "frame_index": item.frame_index,
                    "valid": item.valid,
                    "face_count": item.face_count,
                    "spoofing_detected": item.spoofing_detected,
                    "error_code": item.error_code,
                    "similarity_by_candidate": [
                        {
                            "user_id": similarity.user_id,
                            "employee_id": similarity.employee_id,
                            "similarity": similarity.similarity,
                        }
                        for similarity in item.similarity_by_candidate
                    ],
                }
                for item in response.frames
            ],
        })
        return response


def create_grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    pb2_grpc.add_FaceRecognitionServicer_to_server(FaceRecognitionGrpcService(), server)
    return server
