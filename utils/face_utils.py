"""Xử lý khuôn mặt: Giữ AI xịn nhưng tối ưu RAM cho Streamlit Cloud."""
import numpy as np
from deepface import DeepFace
from cryptography.fernet import Fernet
from PIL import Image
from .constants import FACE_MODEL

def extract_embedding(image_path: str) -> list:
    try:
        # TỐI ƯU 1: Thu nhỏ ảnh về kích thước đầu vào chuẩn của AI (224x224) để giảm RAM
        img = Image.open(image_path).convert('RGB')
        img = img.resize((224, 224), Image.Resampling.LANCZOS)
        img.save(image_path)

        # TỐI ƯU 2: Đổi RetinaFace (119MB) sang YuNet (Siêu nhẹ, tích hợp sẵn trong OpenCV)
        reps = DeepFace.represent(
            img_path=image_path,
            model_name=FACE_MODEL,
            enforce_detection=True, 
            detector_backend="yunet", # Hoặc "ssd" nếu máy báo lỗi không hỗ trợ yunet
        )
        if not reps:
            raise ValueError("Không tìm thấy khuôn mặt trong ảnh.")
        return reps[0]["embedding"]
    except Exception as e:
        raise ValueError("Không tìm thấy khuôn mặt rõ ràng. Vui lòng chụp lại ở nơi đủ sáng, không đeo khẩu trang và nhìn thẳng vào camera.")

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
