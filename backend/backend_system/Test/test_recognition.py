import pymongo

try:
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["Intern"]
    collection = db["employees"]

    # Kiểm tra kết nối
    print("[INFO] Kết nối MongoDB thành công!")

    # Kiểm tra có dữ liệu không
    employees = collection.find()
    for emp in employees:
        print(emp)

except Exception as e:
    print(f"[ERROR] Không thể kết nối MongoDB: {e}")
