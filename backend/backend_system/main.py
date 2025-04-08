from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from logic_business import calculate_salary, get_work_schedule, get_attendance
from config import DATABASE_URL
from database import get_database
from utils.AEShashing import encrypt_embedding, decrypt_embedding
from checkin_checkout import recognize_face
from bson import ObjectId
import cv2
import numpy as np
from pymongo import MongoClient
import datetime
import torch
from employee_register import get_face_embedding
from facenet_pytorch import InceptionResnetV1, MTCNN

app = FastAPI()

client = MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
collection = db["employees"]
# Hàm convert ObjectId -> string (fix lỗi JSON)
def serialize_document(doc):
    doc["_id"] = str(doc["_id"])
    return doc

# Khởi tạo MTCNN và InceptionResnetV1
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(keep_all=False, device=device)
facenet = InceptionResnetV1(pretrained="casia-webface").to(device).eval()


# Lưu embedding vào database
@app.post("/employee/{employee_id}/save_embedding")
async def save_embedding(employee_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    embedding_vector = [0.5] * 128  # Dữ liệu giả định
    encrypted_embedding = encrypt_embedding(embedding_vector)

    await db["employees"].update_one(
        {"employee_id": employee_id},
        {"$set": {"encrypted_embedding": encrypted_embedding}},
        upsert=True
    )
    return {"message": "🔐 Embedding đã được mã hóa và lưu trữ!"}

# API lấy embedding của nhân viên
@app.get("/employee/{employee_id}/get_embedding")   
async def get_embedding(employee_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    employee = await db["employees"].find_one({"employee_id": employee_id})
    if employee and "encrypted_embedding" in employee:
        decrypted_embedding = decrypt_embedding(employee["encrypted_embedding"])
        return {"embedding": decrypted_embedding[:5]}  # Trả về 5 phần tử đầu tiên
    return {"error": "Không tìm thấy embedding!"}

# 💰 API tính lương nhân viên
@app.get("/employee/{employee_id}/salary")
async def api_calculate_salary(employee_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await calculate_salary(employee_id, db)

# 🕒 API kiểm tra lịch làm việc
@app.get("/employee/{employee_id}/work_schedule")
async def api_get_work_schedule(employee_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await get_work_schedule(employee_id, db)

# 📅 API kiểm tra chấm công
@app.get("/employee/{employee_id}/attendance/{month}")
async def api_get_attendance(employee_id: str, month: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await get_attendance(employee_id, month, db)

# API đăng ký nhân viên mới
@app.post("/register/")
async def register_employee(
    image: UploadFile = File(...),
    employee_id: str = Form(...),
    name: str = Form(...),
    address: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
):
    try:
        image_bytes = await image.read()
        embedding = get_face_embedding(image_bytes)

        if embedding is None:
            raise HTTPException(status_code=400, detail="Không thể trích xuất đặc trưng khuôn mặt")

        # Kiểm tra nếu employee_id đã tồn tại
        if collection.find_one({"employee_id": employee_id}):
            return {"status": 0, "message": f"Nhân viên với ID '{employee_id}' đã tồn tại."}

        # Lưu vào MongoDB
        new_employee = {
            "employee_id": employee_id,
            "name": name,
            "address": address,
            "department": department,
            "position": position,
            "email": email,
            "phone": phone,
            "face_embedding": embedding,
        }
        collection.insert_one(new_employee)

        return {"status": 1, "message": "Đăng ký nhân viên thành công!"}
    except Exception as e:
        print("Lỗi server:", e)
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi phía server.")
    
# API nhận diện khuôn mặt
@app.post("/recognize/")
async def recognize(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    result = recognize_face(image)
    return result

# API đăng ký nhân viên và lưu face embedding
@app.post("/employee/{employee_id}/register_with_face")
async def register_employee_with_face(employee_id: str, name: str, email: str, face_embedding: list, db: AsyncIOMotorDatabase = Depends(get_database)):
    # Kiểm tra ID nhân viên đã tồn tại chưa
    existing_employee = await db["employees"].find_one({"employee_id": employee_id})
    if existing_employee:
        raise HTTPException(status_code=400, detail="Mã nhân viên đã tồn tại!")

    # Chuyển face_embedding về Tensor
    face_tensor = torch.tensor(face_embedding, dtype=torch.float32).to(device)
    face_tensor = face_tensor.unsqueeze(0)  # Thêm batch dimension

    # Trích xuất embedding
    with torch.no_grad():
        embedding = facenet(face_tensor).cpu().numpy().tolist()

    # Lưu vào MongoDB
    employee_data = {
        "employee_id": employee_id,
        "name": name,
        "email": email,
        "status": "active",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "embedding": embedding
    }
    
    await db["employees"].insert_one(employee_data)
    return {"message": "Đăng ký nhân viên thành công với khuôn mặt!", "employee_id": employee_id}
