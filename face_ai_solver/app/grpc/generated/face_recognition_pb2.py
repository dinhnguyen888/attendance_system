# -*- coding: utf-8 -*-
"""Dynamic protobuf classes for resp.face FaceRecognition.

This mirrors face_recognition.proto and avoids requiring code generation at
runtime in deployment images.
"""
from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()


def _field(message, name, number, field_type, label=1, type_name=None):
    item = message.field.add()
    item.name = name
    item.number = number
    item.label = label
    item.type = field_type
    if type_name:
        item.type_name = type_name


def _build_file():
    file_proto = _descriptor_pb2.FileDescriptorProto()
    file_proto.name = "face_recognition.proto"
    file_proto.package = "resp.face"
    file_proto.syntax = "proto3"

    msg = file_proto.message_type.add()
    msg.name = "FaceBox"
    _field(msg, "x", 1, 5)
    _field(msg, "y", 2, 5)
    _field(msg, "width", 3, 5)
    _field(msg, "height", 4, 5)

    msg = file_proto.message_type.add()
    msg.name = "Candidate"
    _field(msg, "user_id", 1, 3)
    _field(msg, "employee_id", 2, 3)
    _field(msg, "registered_embedding", 3, 2, label=3)
    _field(msg, "threshold", 4, 2)

    msg = file_proto.message_type.add()
    msg.name = "CandidateSimilarity"
    _field(msg, "user_id", 1, 3)
    _field(msg, "employee_id", 2, 3)
    _field(msg, "similarity", 3, 2)

    msg = file_proto.message_type.add()
    msg.name = "CandidateMetrics"
    _field(msg, "user_id", 1, 3)
    _field(msg, "employee_id", 2, 3)
    _field(msg, "threshold", 3, 2)
    _field(msg, "max_similarity", 4, 2)
    _field(msg, "avg_similarity", 5, 2)
    _field(msg, "min_similarity", 6, 2)
    _field(msg, "similarity_margin", 7, 2)

    msg = file_proto.message_type.add()
    msg.name = "FrameMetrics"
    _field(msg, "frame_index", 1, 5)
    _field(msg, "valid", 2, 8)
    _field(msg, "face_count", 3, 5)
    _field(msg, "spoofing_detected", 4, 8)
    _field(msg, "error_code", 5, 9)
    _field(msg, "similarity_by_candidate", 6, 11, label=3, type_name=".resp.face.CandidateSimilarity")

    msg = file_proto.message_type.add()
    msg.name = "RegisterFaceRequest"
    _field(msg, "employee_id", 1, 3)
    _field(msg, "image_bytes", 2, 12)
    _field(msg, "image_mime", 3, 9)

    msg = file_proto.message_type.add()
    msg.name = "RegisterFaceResponse"
    _field(msg, "status", 1, 9)
    _field(msg, "error_code", 2, 9)
    _field(msg, "message", 3, 9)
    _field(msg, "embedding", 4, 2, label=3)
    _field(msg, "embedding_dim", 5, 5)
    _field(msg, "model_name", 6, 9)
    _field(msg, "face_count", 7, 5)
    _field(msg, "face_box", 8, 11, type_name=".resp.face.FaceBox")
    _field(msg, "blur_score", 9, 2)
    _field(msg, "brightness_score", 10, 2)

    msg = file_proto.message_type.add()
    msg.name = "AnalyzeFaceRequest"
    _field(msg, "video_bytes", 1, 12)
    _field(msg, "video_mime", 2, 9)
    _field(msg, "max_frames", 3, 5)
    _field(msg, "candidates", 4, 11, label=3, type_name=".resp.face.Candidate")

    msg = file_proto.message_type.add()
    msg.name = "AnalyzeFaceResponse"
    _field(msg, "status", 1, 9)
    _field(msg, "error_code", 2, 9)
    _field(msg, "message", 3, 9)
    _field(msg, "processed_frame_count", 4, 5)
    _field(msg, "valid_frame_count", 5, 5)
    _field(msg, "spoofed_frame_count", 6, 5)
    _field(msg, "spoofing_error_rate", 7, 2)
    _field(msg, "best_candidate_user_id", 8, 3)
    _field(msg, "best_candidate_employee_id", 9, 3)
    _field(msg, "max_similarity", 10, 2)
    _field(msg, "avg_similarity", 11, 2)
    _field(msg, "min_similarity", 12, 2)
    _field(msg, "best_frame_index", 13, 5)
    _field(msg, "candidates", 14, 11, label=3, type_name=".resp.face.CandidateMetrics")
    _field(msg, "frames", 15, 11, label=3, type_name=".resp.face.FrameMetrics")

    service = file_proto.service.add()
    service.name = "FaceRecognition"
    method = service.method.add()
    method.name = "RegisterFace"
    method.input_type = ".resp.face.RegisterFaceRequest"
    method.output_type = ".resp.face.RegisterFaceResponse"
    method = service.method.add()
    method.name = "AnalyzeFace"
    method.input_type = ".resp.face.AnalyzeFaceRequest"
    method.output_type = ".resp.face.AnalyzeFaceResponse"
    return file_proto


_pool = _descriptor_pool.Default()
try:
    DESCRIPTOR = _pool.AddSerializedFile(_build_file().SerializeToString())
except TypeError:
    DESCRIPTOR = _pool.FindFileByName("face_recognition.proto")


def _message_class(name):
    cls = _reflection.GeneratedProtocolMessageType(
        name,
        (_message.Message,),
        {"DESCRIPTOR": DESCRIPTOR.message_types_by_name[name], "__module__": __name__},
    )
    _sym_db.RegisterMessage(cls)
    return cls


FaceBox = _message_class("FaceBox")
Candidate = _message_class("Candidate")
CandidateSimilarity = _message_class("CandidateSimilarity")
CandidateMetrics = _message_class("CandidateMetrics")
FrameMetrics = _message_class("FrameMetrics")
RegisterFaceRequest = _message_class("RegisterFaceRequest")
RegisterFaceResponse = _message_class("RegisterFaceResponse")
AnalyzeFaceRequest = _message_class("AnalyzeFaceRequest")
AnalyzeFaceResponse = _message_class("AnalyzeFaceResponse")
