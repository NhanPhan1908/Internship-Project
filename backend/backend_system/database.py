from pymongo import MongoClient
from config import DATABASE_URL
from fastapi import Depends
import numpy as np

# Kết nối MongoDB
client = MongoClient(DATABASE_URL)
db = client["Intern"]  

# Các collection (bảng dữ liệu)
employees_collection = db["employees"]
attendance_collection = db["attendance"]
salary_collection = db["salary"]
work_schedule_collection = db["work_schedule"]
checkin_collection = db["checkin"]
checkout_collection = db["checkout"]

def load_embeddings_from_db():
    embeddings, names = [], []
    for record in employees_collection.find({}, {"name": 1, "embedding": 1}):
        if "embedding" not in record:
            continue
        names.append(record["name"])
        embeddings.append(np.array(record["embedding"]))
    return (np.array(embeddings), names) if embeddings else (None, None)

def get_database(path: str, db_name: str):
    collection = client[db_name][path]
    data = collection.find_one({"path": path})
    if data is None:
        return {"message": "Không tìm thấy dữ liệu!"}
    return db