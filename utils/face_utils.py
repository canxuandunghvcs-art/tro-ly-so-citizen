"""Xử lý khuôn mặt: trích xuất embedding, mã hóa/giải mã, so khớp."""
import numpy as np
from deepface import DeepFace
from cryptography.fernet import Fernet
from .constants import FACE_MODEL, DETECTOR_BACKEND


def extract_embedding(image_path: str) -> list:
    reps = DeepFace.represent(
        img_path=image_path,
        model_name=FACE_MODEL,
        enforce_detection=False,
        detector_backend=DETECTOR_BACKEND,
    )
    if not reps:
        raise ValueError("Không tìm thấy khuôn mặt trong ảnh.")
    return reps[0]["embedding"]


def cosine_similarity(a, b) -> float:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
    return float(np.dot(a, b) / denom)


def encrypt_embedding(embedding, key: str) -> str:
    f = Fernet(key.encode() if isinstance(key, str) else key)
    raw = np.asarray(embedding, dtype=np.float32).tobytes()
    return f.encrypt(raw).decode()


def decrypt_embedding(token: str, key: str) -> np.ndarray:
    f = Fernet(key.encode() if isinstance(key, str) else key)
    raw = f.decrypt(token.encode())
    return np.frombuffer(raw, dtype=np.float32)