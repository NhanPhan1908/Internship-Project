from fastapi import FastAPI, UploadFile, Form, HTTPException, File 
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional
from facenet_pytorch import InceptionResnetV1, MTCNN
from PIL import Image
import torch
import numpy as np
import io

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
collection = db["employees"]

# Model nhận diện khuôn mặt
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
facenet = InceptionResnetV1(pretrained='casia-webface').eval().to(device)
mtcnn = MTCNN(image_size=160, margin=0, device=device)

# Khởi tạo FastAPI
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👉 Hàm xử lý ảnh và tạo embedding
def get_face_embedding(image_bytes):
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        face = mtcnn(pil_img)
        if face is None:
            print("❌ Không phát hiện khuôn mặt!")
            return None

        face = face.unsqueeze(0).to(device)

        with torch.no_grad():
            embedding = facenet(face).cpu().numpy()[0]

        if np.isnan(embedding).any():
            print("❌ Embedding chứa giá trị NaN.")
            return None

        return embedding.tolist()
    
    except Exception as e:
        print("Lỗi xử lý ảnh:", e)
        return None
