# -*- coding: utf-8 -*-
import grpc

from . import face_recognition_pb2 as face__recognition__pb2


class FaceRecognitionStub:
    def __init__(self, channel):
        self.RegisterFace = channel.unary_unary(
            "/resp.face.FaceRecognition/RegisterFace",
            request_serializer=face__recognition__pb2.RegisterFaceRequest.SerializeToString,
            response_deserializer=face__recognition__pb2.RegisterFaceResponse.FromString,
        )
        self.AnalyzeFace = channel.unary_unary(
            "/resp.face.FaceRecognition/AnalyzeFace",
            request_serializer=face__recognition__pb2.AnalyzeFaceRequest.SerializeToString,
            response_deserializer=face__recognition__pb2.AnalyzeFaceResponse.FromString,
        )
