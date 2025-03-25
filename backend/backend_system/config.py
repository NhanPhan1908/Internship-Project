from pymongo import MongoClient

# Thay đổi URL này nếu bạn dùng MongoDB Atlas hoặc có user/password
DATABASE_URL = "mongodb://localhost:27017"

# Kết nối đến MongoDB
client = MongoClient(DATABASE_URL)

# Chọn database
db = client["workspace_db"]

# Khai báo các collection (bảng dữ liệu)
employees_collection = db["employees"]
attendance_collection = db["attendance"]
salary_collection = db["salary"]
work_schedule_collection = db["work_schedule"]
# Test kết nối

print("✅ Kết nối MongoDB thành công!")
