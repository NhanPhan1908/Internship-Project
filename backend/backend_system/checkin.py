from datetime import datetime
import cv2
import numpy as np
from pymongo import MongoClient
from PIL import Image
import torch
from scipy.spatial.distance import cosine
from facenet_pytorch import MTCNN, InceptionResnetV1
from torchvision import transforms

# 🎯 Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["attendance"]
collection_employees = db["employees"]  # Sửa lỗi tên collection
collection_checkin = db["checkin"]
collection_checkout = db["checkout"]

# 📌 Cấu hình giờ làm
CHECKIN_START = 8      # Check-in sớm nhất
LATE_CHECKIN_LIMIT = 9 # Trễ nhất được phép check-in
CHECKOUT_HOUR = 17     # Check-out sớm nhất

# 🖥 Kiểm tra GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(keep_all=False, device=device)
facenet = InceptionResnetV1(pretrained="casia-webface").eval().to(device)

# 📌 Tiền xử lý ảnh
def fixed_image_standardization(image_tensor):
    return (image_tensor - 127.5) / 128.0

def trans(img):
    transform = transforms.Compose([
        transforms.Resize((160, 160)),  # Resize để phù hợp với model
        transforms.ToTensor(),
        fixed_image_standardization
    ])
    return transform(img)

# 🔍 Tải embeddings từ database
def load_embeddings_from_db():
    embeddings = []
    names = []

    for record in collection_employees.find({}, {"name": 1, "embedding": 1, "_id": 0}):
        names.append(record["name"])
        embeddings.append(np.array(record["embedding"]))  # Chuyển sang NumPy array luôn

    if len(embeddings) == 0:
        return None, None  # Trả về None nếu không có dữ liệu

    return np.array(embeddings), names  # Trả về NumPy array

# 🕒 Xử lý check-in/check-out
def save_attendance(name, confidence):
    now = datetime.now()
    hour, minute = now.hour, now.minute
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    if hour < LATE_CHECKIN_LIMIT:  # Check-in (Trước 09:00)
        late_minutes = max(0, (hour - CHECKIN_START) * 60 + minute)
        collection_checkin.insert_one({
            "name": name,
            "confidence": confidence,
            "timestamp": timestamp,
            "late_minutes": late_minutes
        })
        print(f"✅ Check-in: {name} - Đi muộn {late_minutes} phút")

    elif hour >= CHECKOUT_HOUR:  # Check-out (Sau 17:00)
        collection_checkout.insert_one({
            "name": name,
            "confidence": confidence,
            "timestamp": timestamp
        })
        print(f"✅ Check-out: {name}")

    else:  # Không thể chấm công ngoài thời gian quy định
        print(f"🚫 {name} không thể chấm công vào thời gian này ({timestamp})")

# 🎭 Nhận diện khuôn mặt
def recognize_face(frame):
    embeddings, names = load_embeddings_from_db()
    if embeddings is None:
        return

    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    face = mtcnn(image)

    if face is None:
        print("❌ Không phát hiện khuôn mặt! Vui lòng thử lại.")
        return

    face_tensor = trans(face).unsqueeze(0).to(device)

    with torch.no_grad():
        new_embedding = facenet(face_tensor).cpu().numpy().flatten()

    similarities = [1 - cosine(new_embedding, emb.flatten()) for emb in embeddings]
    best_match = np.argmax(similarities)

    if similarities[best_match] > 0.5:  # Ngưỡng nhận diện chính xác hơn
        name = names[best_match]
        confidence = similarities[best_match]
        print(f"✅ Nhận diện thành công: {name} ({confidence:.2f})")
        save_attendance(name, confidence)
    else:
        print("❌ Không tìm thấy nhân viên trong hệ thống.")

# 🎥 Mở camera và chấm công
def capture_and_recognize():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("📸 Nhìn vào camera để chấm công. Nhấn 'SPACE' để chụp ảnh, 'ESC' để thoát.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Lỗi camera! Kiểm tra lại kết nối.")
            break

        boxes, _ = mtcnn.detect(frame)
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.imshow("Face Recognition", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # Space
            print("🕵️‍♂️ Đang nhận diện...")
            recognize_face(frame)

        elif key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

# 🚀 Chạy chương trình
if __name__ == "__main__":
    capture_and_recognize()
