from pymongo import MongoClient

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Thay đổi nếu cần
db = client["Intern"]
collection = db["employees"]

print("✅ Kết nối MongoDB thành công!")

# Hàm lấy thông tin nhân viên theo ID
def get_employee_by_id(employee_id):
    print(f"🔍 Đang tìm nhân viên với ID: {employee_id}")
    employee = collection.find_one({"employee_id": employee_id})
    if employee:
        print(f"✅ Tìm thấy nhân viên: {employee}")
    else:
        print("❌ Không tìm thấy nhân viên!")

# Nhập Employee ID cần tìm
emp_id = input("Nhập Employee ID: ").strip()
get_employee_by_id(emp_id)
