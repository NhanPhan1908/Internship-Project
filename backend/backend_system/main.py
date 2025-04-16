from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from logic_business import calculate_salary, get_work_schedule, get_attendance
from config import DATABASE_URL
from database import get_database
from bson import ObjectId   
from utils.AEShashing import encrypt_embedding, decrypt_embedding
from checkin_checkout import recognize_face
from util import get_late_minute
from anti_spoofing import anti_spoofing
import cv2
from model import xception
import numpy as np
from pymongo import MongoClient
from datetime import datetime
import torch
from employee_register import get_face_embedding
from facenet_pytorch import InceptionResnetV1, MTCNN

app = FastAPI()

client = MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
employees_collection = db["employees"]
attendance_collection = db["attendance"]
checkin_collection = db["checkin"]
checkout_collection = db["checkout"]



# Khởi tạo MTCNN và InceptionResnetV1
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(keep_all=False, device=device)
facenet = InceptionResnetV1(pretrained="casia-webface").to(device).eval()



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
        if employees_collection.find_one({"employee_id": employee_id}):
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
            "embedding": embedding,
        }
        employees_collection.insert_one(new_employee)

        return {"status": 1, "message": "Đăng ký nhân viên thành công!"}
    except Exception as e:
        print("Lỗi server:", e)
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi phía server.")
    
# API nhận diện khuôn mặt


@app.post("/recognize/")
async def recognize(file: UploadFile = File(...)):
    # Đọc ảnh từ file tải lên
    image_bytes = await file.read()
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    # Bước 1: Nhận diện khuôn mặt
    result = recognize_face(image)
    
    if not result["detect"]:
        raise HTTPException(status_code=400, detail="Không phát hiện khuôn mặt")
    
    if not result["recognize"]:
        raise HTTPException(status_code=400, detail="Không nhận diện được nhân viên")
    
    employee_id = result.get("employee_id")
    name = result.get("name")
    confidence = result.get("confidence", "N/A")

    # Bước 2: Kiểm tra giả mạo (anti-spoofing)
    is_real = anti_spoofing(image) 
    
    if not is_real:
        raise HTTPException(status_code=400, detail="Khuôn mặt giả mạo, không thể tiếp tục")

    # Bước 3: Lưu thông tin vào cơ sở dữ liệu
    new_attendance = {
        "employee_id": employee_id,
        "name": name,
        "confidence": confidence,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "checkin"
    }
    attendance_collection.insert_one(new_attendance)

    new_checkin = {
        "employee_id": employee_id,
        "name": name,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "late_time": get_late_minute()
    }
    checkin_collection.insert_one(new_checkin)

    # Trả về kết quả nhận diện và thông tin check-in
    return {
        "status": result["status"],
        "detect": result["detect"],
        "recognize": result["recognize"],
        "name": name,
        "confidence": confidence,
        "employee_id": employee_id,
        "message": result["message"]
    }
