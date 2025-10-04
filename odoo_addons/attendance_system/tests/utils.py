# -*- coding: utf-8 -*-
"""
Utils cho unit tests: load ảnh test từ thư mục và encode base64.
Nếu không tìm thấy ảnh, trả về một chuỗi base64 placeholder hợp lệ để test không bị fail vì thiếu ảnh.
"""

import os
import base64

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


def load_base64_from_dir(dir_path):
    """Tìm file ảnh đầu tiên trong dir_path và trả về dạng data:image/jpeg;base64,xxx
    Nếu không tìm thấy, trả về placeholder base64.
    """
    if not os.path.isdir(dir_path):
        return placeholder_image()
    
    for name in sorted(os.listdir(dir_path)):
        ext = os.path.splitext(name)[1].lower()
        if ext in SUPPORTED_EXTS:
            abs_path = os.path.join(dir_path, name)
            try:
                with open(abs_path, 'rb') as f:
                    data = f.read()
                b64 = base64.b64encode(data).decode('utf-8')
                mime = 'image/jpeg' if ext in {'.jpg', '.jpeg'} else 'image/png'
                return f'data:{mime};base64,{b64}'
            except Exception:
                # Nếu đọc lỗi, dùng placeholder
                return placeholder_image()
    
    return placeholder_image()


def placeholder_image():
    """Trả về một base64 placeholder (nội dung không phải ảnh thật, nhưng đủ để test vì API đã được mock)."""
    return 'data:image/jpeg;base64,' + base64.b64encode(b'placeholder').decode('utf-8')


def path_from_tests(*parts):
    """Trả về đường dẫn tuyệt đối từ thư mục chứa file utils này."""
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, *parts)


def get_check_in_image(case_folder):
    """Lấy ảnh cho nhóm check_in theo tên thư mục con."""
    return load_base64_from_dir(path_from_tests('test_data', 'check_in', case_folder))


def get_register_image(case_folder):
    """Lấy ảnh cho nhóm register theo tên thư mục con."""
    return load_base64_from_dir(path_from_tests('test_data', 'register', case_folder))
