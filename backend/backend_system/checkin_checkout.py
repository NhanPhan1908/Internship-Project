import cv2
import numpy as np
from PIL import Image
import torch
from scipy.spatial.distance import cosine
from model import mtcnn, facenet
from database import load_embeddings_from_db

def recognize_face(image: np.array):
    embeddings, names, employee_id = load_embeddings_from_db()
    if embeddings is None or names is None:
        return {
            "status": "fail",
            "detect": False,
            "recognize": False,
            "message": "Không có dữ liệu nhận diện!"
        }

    # Chuyển ảnh sang định dạng PIL
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    # Phát hiện khuôn mặt
    face = mtcnn(pil_img)
    
    if face is None:
        return {
            "status": "ok",
            "detect": False,
            "recognize": False,
            "message": "Không phát hiện khuôn mặt!"
        }

    # Nhận diện khuôn mặt
    face = face.unsqueeze(0).to("cuda" if torch.cuda.is_available() else "cpu")

    with torch.no_grad():
        new_embedding = facenet(face).cpu().numpy().flatten()

    # Chuyển embedding thành list
    new_embedding = new_embedding.tolist()

    similarities = [1 - cosine(new_embedding, emb.flatten()) for emb in embeddings]
    best_match = np.argmax(similarities)
    confidence = similarities[best_match]
    if confidence > 0.8:
        return {
            "status": "ok",
            "detect": True,
            "recognize": True,
            "name": names[best_match],
            "employee_id": employee_id[best_match],  
            "confidence": round(confidence, 4),
            "message": f"Đã nhận diện thành công"
        }
    else:
        return {
            "status": "ok",
            "detect": True,
            "recognize": False,
            "message": "Không tìm thấy nhân viên!"
        }
