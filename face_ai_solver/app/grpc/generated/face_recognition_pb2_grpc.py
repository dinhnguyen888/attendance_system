# -*- coding: utf-8 -*-
"""gRPC bindings for resp.face FaceRecognition."""
import grpc

from app.grpc.generated import face_recognition_pb2 as face__recognition__pb2


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


class FaceRecognitionServicer:
    def RegisterFace(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented")
        raise NotImplementedError("Method not implemented")

    def AnalyzeFace(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented")
        raise NotImplementedError("Method not implemented")


def add_FaceRecognitionServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "RegisterFace": grpc.unary_unary_rpc_method_handler(
            servicer.RegisterFace,
            request_deserializer=face__recognition__pb2.RegisterFaceRequest.FromString,
            response_serializer=face__recognition__pb2.RegisterFaceResponse.SerializeToString,
        ),
        "AnalyzeFace": grpc.unary_unary_rpc_method_handler(
            servicer.AnalyzeFace,
            request_deserializer=face__recognition__pb2.AnalyzeFaceRequest.FromString,
            response_serializer=face__recognition__pb2.AnalyzeFaceResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "resp.face.FaceRecognition", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))
