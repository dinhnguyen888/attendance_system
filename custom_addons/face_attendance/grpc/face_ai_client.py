import grpc

from . import face_recognition_pb2 as pb2
from . import face_recognition_pb2_grpc as pb2_grpc


class FaceAiClient:
    def __init__(self, target, timeout=15):
        self.target = target
        self.timeout = timeout

    def register_face(self, employee_id, image_bytes, image_mime="image/png"):
        with grpc.insecure_channel(self.target) as channel:
            stub = pb2_grpc.FaceRecognitionStub(channel)
            return stub.RegisterFace(
                pb2.RegisterFaceRequest(
                    employee_id=int(employee_id),
                    image_bytes=image_bytes,
                    image_mime=image_mime or "image/png",
                ),
                timeout=self.timeout,
            )

    def analyze_face(self, video_bytes, video_mime, candidates, max_frames=7):
        request = pb2.AnalyzeFaceRequest(
            video_bytes=video_bytes,
            video_mime=video_mime or "video/webm",
            max_frames=int(max_frames or 7),
        )
        for candidate in candidates:
            request.candidates.append(
                pb2.Candidate(
                    user_id=int(candidate["user_id"]),
                    employee_id=int(candidate["employee_id"]),
                    registered_embedding=[float(value) for value in candidate["registered_embedding"]],
                    threshold=float(candidate["threshold"]),
                )
            )
        with grpc.insecure_channel(self.target) as channel:
            stub = pb2_grpc.FaceRecognitionStub(channel)
            return stub.AnalyzeFace(request, timeout=self.timeout)
