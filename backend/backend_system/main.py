from fastapi import FastAPI, Depends, APIRouter, HTTPException
from database import get_database
from config import DATABASE_URL
from motor.motor_asyncio import AsyncIOMotorDatabase
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

    return serialize_document(employee)async def get_employee(employee_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    employee = await db["employees"].find_one({"employee_id": employee_id})
    if not employee:
        return {"error": "Không tìm thấy nhân viên"}
    return employee

