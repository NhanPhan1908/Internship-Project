from fastapi import FastAPI, UploadFile, Form, HTTPException, File 
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional
from facenet_pytorch import InceptionResnetV1
from PIL import Image
import torch
import numpy as np
import io
import cv2

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
collection = db["employees"]

# Model nhận diện khuôn mặt
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
facenet = InceptionResnetV1(pretrained='casia-webface').eval().to(device)

# Khởi tạo FastAPI
app = FastAPI()

# CORS cho phép frontend truy cập (nếu frontend khác domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hàm chuyển ảnh thành face embedding
def get_face_embedding(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = np.array(img)

        # Resize và xử lý ảnh
        img = cv2.resize(img, (160, 160))  # Kích thước chuẩn cho Facenet
        img = img / 255.0
        img = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0).to(device)

        with torch.no_grad():
            embedding = facenet(img).cpu().numpy()[0]
        return embedding.tolist()
    except Exception as e:
        print("Lỗi xử lý ảnh:", e)
        return None

# Endpoint để đăng ký nhân viên

