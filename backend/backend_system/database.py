from pymongo import MongoClient
from config import DATABASE_URL
from fastapi import Depends
# Kết nối MongoDB
client = MongoClient(DATABASE_URL)
db = client["workspace_db"]

# Các collection (bảng dữ liệu)
employees_collection = db["employees"]
attendance_collection = db["attendance"]
salary_collection = db["salary"]
work_schedule_collection = db["work_schedule"]

def get_database():
    """Hàm trả về database đã kết nối"""
    return db

