import cv2
import numpy as np
from PIL import Image
import torch
from scipy.spatial.distance import cosine
from model import mtcnn, facenet
from database import load_embeddings_from_db

def recognize_face(image: np.array):
    embeddings, names = load_embeddings_from_db()
    if embeddings is None or names is None:
        return {"message": "Không có dữ liệu nhận diện!"}

    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    face = mtcnn(pil_img)
    
    if face is None:
        return {"message": "Không phát hiện khuôn mặt!"}

    face = face.unsqueeze(0).to("cuda" if torch.cuda.is_available() else "cpu")

    with torch.no_grad():
        new_embedding = facenet(face).cpu().numpy().flatten()

    similarities = [1 - cosine(new_embedding, emb.flatten()) for emb in embeddings]
    best_match = np.argmax(similarities)

    if similarities[best_match] > 0.3:
        return {"name": names[best_match], "confidence": similarities[best_match]}
    return {"message": "Không tìm thấy nhân viên!"}
