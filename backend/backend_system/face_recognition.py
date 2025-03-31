import cv2
import torch
import numpy as np
from facenet_pytorch import InceptionResnetV1, MTCNN
from torchvision import transforms
from scipy.spatial.distance import cosine
from PIL import Image
import os
import pymongo
from datetime import datetime


DATA_PATH = './data'
os.makedirs(DATA_PATH, exist_ok=True)

# connecet database
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
collection_employees = db["employees"]  # Collection chứa embedding
collection_attendance = db["attendance"]  # Collection chứa dữ liệu chấm công

# check GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Init model
mtcnn = MTCNN(keep_all=False, device=device)
facenet = InceptionResnetV1(pretrained="casia-webface").to(device).eval()

# Model Init
def fixed_image_standardization(image_tensor):
    return (image_tensor - 127.5) / 128.0

def trans(img):
    """ Chuyển đổi ảnh thành tensor nếu chưa phải """
    if isinstance(img, torch.Tensor):
        return img  # Nếu đã là tensor, không cần chuyển đổi
    transform = transforms.Compose([
        transforms.ToTensor(),
        fixed_image_standardization
    ])
    return transform(img)

# List employees embeddings từ MongoDB (collection employees)
def load_embeddings_from_db():
    embeddings = []
    names = []

    for record in collection_employees.find({}, {"name": 1, "embedding": 1, "_id": 0}):
        names.append(record["name"])
        embeddings.append(np.array(record["embedding"]))  # Chuyển sang NumPy array luôn

    if len(embeddings) == 0:
        return None, None  # Trả về None nếu không có dữ liệu

    return np.array(embeddings), names  # Trả về NumPy array

# Save attendance vào MongoDB (collection attendance)
def save_to_attendance(name, confidence):
    data = {
        "name": name,
        "confidence": confidence,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    collection_attendance.insert_one(data)
    print(f"✅ Đã lưu vào attendance: {data}")

# Capture and reconize
def capture_and_recognize():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Hãy nhìn vào camera. Nhấn 'SPACE' để chụp ảnh, 'ESC' để thoát.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera lỗi!")
            break

        boxes, _ = mtcnn.detect(frame)
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) # Vẽ khung
                cv2.putText(frame, "Detected", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                # Đánh dấu "Detected"

        cv2.imshow("Capture Face", frame) #hien thi camera
        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # Space
            print("Đang nhận diện...")
            recognize_face(frame)

        elif key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()


def recognize_face(frame):
    embeddings, names = load_embeddings_from_db() ## Lấy danh sách embedding từ MongoDB

    if embeddings is None:
        print(" Không tìm thấy dữ liệu nhận diện trong MongoDB!") 
        return

    # Chuyển frame thành ảnh PIL
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)) ## Chuyển đổi từ BGR (OpenCV) sang RGB (PIL)
    face = mtcnn(image)

    if face is None:
        print(" Không phát hiện khuôn mặt! Vui lòng thử lại.")
        return  # Yêu cầu quét lại thay vì tiếp tục xử lý

    # Chuyển tensor thành tensor chuẩn hóa
    face_tensor = trans(face).unsqueeze(0).to(device) # Thêm batch dimension

    # Tính embedding mới
    with torch.no_grad():
        new_embedding = facenet(face_tensor).cpu().numpy().flatten()  # Flatten thành vector 1D

    # cosine simirarities
    similarities = [1 - cosine(new_embedding, emb.flatten()) for emb in embeddings]  # Flatten embeddings cũ
    best_match = np.argmax(similarities)

    # Xác định danh tính
    if similarities[best_match] > 0.3:
        name = names[best_match]
        confidence = similarities[best_match]
        print(f"✅ Nhận diện thành công: {name} ({confidence:.2f})")
        color = (0, 255, 0)

        # Lưu vào database nếu nhận diện thành công
        save_to_attendance(name, confidence)

    else:
        print(" Không tìm thấy nhân viên! Vui lòng thử lại.")
        return  # Không lưu vào database và yêu cầu quét lại

    # 📌 Hiển thị bounding box với tên nhân viên
    boxes, _ = mtcnn.detect(frame)
    if boxes is not None:
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow("Recognition Result", frame)
    cv2.waitKey(2000)


# 📌 Chạy chương trình
if __name__ == "__main__":
    capture_and_recognize()
