from bson import ObjectId
from fastapi import FastAPI, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_database
from logic_business import calculate_salary, get_work_schedule, get_attendance
from config import DATABASE_URL
from utils.AEShashing import encrypt_embedding, decrypt_embedding

app = FastAPI()

# Hàm convert ObjectId -> string (fix lỗi JSON)
def serialize_document(doc):
    doc["_id"] = str(doc["_id"])
    return doc

# API lấy danh sách nhân viên
@app.get("/employees")
async def get_employees(db: AsyncIOMotorDatabase = Depends(get_database)):
    employees = await db["employees"].find().to_list(100)  # Lấy tối đa 100 nhân viên
    return {"data": employees}

# API lấy một nhân viên theo ID
@app.get("/employee/{employee_id}")
async def get_employee(employee_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        object_id = ObjectId(employee_id)  # Chuyển sang ObjectId
    except Exception:
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    employee = await db["employees"].find_one({"_id": object_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")

    return serialize_document(employee)

# API lấy một nhân viên theo employee_id
@app.get("/employee/{employee_id}/info")
async def get_employee_by_id(employee_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    employee = await db["employees"].find_one({"employee_id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    return serialize_document(employee)

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
