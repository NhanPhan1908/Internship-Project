from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from face_recognition import verify_face

#💰 Tính lương nhân viên
#async def calculate_salary(employee_id: str, db: AsyncIOMotorDatabase):
 #   salary = await db["salary"].find_one({"employee_id": employee_id})
  #  if not salary:
   #     return {"status": 0, "message": "🚫 Không tìm thấy thông tin lương!"}
  #  return salary

# 🕒 Kiểm tra lịch làm việc
#async def get_work_schedule(employee_id: str, db: AsyncIOMotorDatabase):
 #   schedule = await db["work_schedule"].find_one({"employee_id": employee_id})
  #  if not schedule:
   #     return {"status": 0, "message": "🚫 Không tìm thấy lịch làm việc!"}
    #return schedule

# 📅 Kiểm tra chấm công
#async def get_attendance(employee_id: str, month: str, db: AsyncIOMotorDatabase):
 #   attendance = await db["attendance"].find_one({"employee_id": employee_id, "month": month})
  ###return attendance

# ✅ Xử lý điểm danh bằng gương mặt
async def face_attendance(employee_id: str, face_embedding, db: AsyncIOMotorDatabase):
    # 1️⃣ Tìm nhân viên
    employee = await db["employees"].find_one({"employee_id": employee_id})
    if not employee or "encrypted_embedding" not in employee:
        return {"status": 0, "message": "🚫 Không tìm thấy nhân viên!"}

    # 2️⃣ Xác thực khuôn mặt
    is_verified = verify_face(employee["encrypted_embedding"], face_embedding)
    if not is_verified:
        return {"status": 0, "message": "🚫 Xác thực thất bại!"}

    # 3️⃣ Cập nhật bảng attendance
    today = datetime.today().strftime("%Y-%m-%d")
    month = datetime.today().strftime("%Y-%m")

    attendance_record = await db["attendance"].find_one({"employee_id": employee_id, "month": month})
    
    if not attendance_record:
        new_attendance = {
            "employee_id": employee_id,
            "month": month,
            "days_present": 1,
            "attendance_log": [today]
        }
        await db["attendance"].insert_one(new_attendance)
    else:
        if today not in attendance_record["attendance_log"]:
            attendance_record["days_present"] += 1
            attendance_record["attendance_log"].append(today)
            await db["attendance"].update_one(
                {"employee_id": employee_id, "month": month},
                {"$set": {"days_present": attendance_record["days_present"], "attendance_log": attendance_record["attendance_log"]}}
            )

    return {"status": 1, "message": "✅ Điểm danh thành công!"}
