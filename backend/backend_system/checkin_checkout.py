import cv2
import torch
import numpy as np
from facenet_pytorch import InceptionResnetV1, MTCNN
from torchvision import transforms
from scipy.spatial.distance import cosine
from PIL import Image
from anti_spoofing import anti_spoofing, anti_spoofing_model
import os
import sys
import pymongo
from datetime import datetime

# Khởi tạo đường dẫn
DATA_PATH = './data'
os.makedirs(DATA_PATH, exist_ok=True)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

# connect database
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Intern"] #database
collection_employees = db["employees"]  # employees collection
collection_checkin = db["checkin"]      # checkin collection
collection_checkout = db["checkout"]    # checkout collection

# check GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# MTCNN and Facenet Model Init
mtcnn = MTCNN(keep_all=False, device=device)
facenet = InceptionResnetV1(pretrained="casia-webface").to(device).eval()

#standardize
def fixed_image_standardization(image_tensor):
    return (image_tensor - 127.5) / 128.0

def trans(img):
    # Chuyển đổi ảnh thành tensor và chuẩn hóa
    if isinstance(img, torch.Tensor):
        return img  # Nếu đã là tensor, không cần chuyển đổi
    transform = transforms.Compose([
        transforms.ToTensor(),
        fixed_image_standardization
    ])
    return transform(img)

def load_embeddings_from_db():
    embeddings = []
    names = []

    for record in collection_employees.find({}, {"name": 1, "embedding": 1}):
        if "embedding" not in record:  
            print(f"⚠️ Cảnh báo: Bản ghi {record.get('name', 'Không tên')} không có embedding. Bỏ qua!")
            continue  # Bỏ qua bản ghi này

        names.append(record["name"])
        embeddings.append(np.array(record["embedding"]))

    if not embeddings:
        return None, None  

    return np.array(embeddings), names

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_hour():
    return datetime.now().hour

def save_to_checkin(name, confidence, late_minute):
    data = {
        "name": name,
        "confidence": confidence,
        "timestamp": get_current_time(),
        "late_minute": late_minute
    }
    collection_checkin.insert_one(data)
    print(f"✅ Đã lưu vào check-in: {data}")

def save_to_checkout(name, confidence):
    data = {
        "name": name,
        "confidence": confidence,
        "timestamp": get_current_time()
    }
    collection_checkout.insert_one(data)
    print(f"✅ Đã lưu vào check-out: {data}")

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
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, "Detected", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.imshow("Capture Face", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 32:
            print("Đang nhận diện...")
            recognize_face(frame)
        elif key == 27:
            break
    cap.release()
    cv2.destroyAllWindows()

def recognize_face(frame):
    embeddings, names = load_embeddings_from_db()
    if embeddings is None:
        print("Không tìm thấy dữ liệu nhận diện trong MongoDB!")
        return
    
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    face = mtcnn(image)
    if face is None:
        print("Không phát hiện khuôn mặt! Vui lòng thử lại.")
        return
    
    is_real = anti_spoofing(frame, anti_spoofing_model)
    if not is_real:
        print("Cảnh báo: Phát hiện giả mạo! Không cho phép nhận diện.")
        return
    
    face_tensor = trans(face).unsqueeze(0).to(device)
    with torch.no_grad():
        new_embedding = facenet(face_tensor).cpu().numpy().flatten()
    
    similarities = [1 - cosine(new_embedding, emb.flatten()) for emb in embeddings]
    best_match = np.argmax(similarities)
    
    if similarities[best_match] > 0.3:
        name, confidence = names[best_match], similarities[best_match]
        print(f"✅ Nhận diện thành công: {name} ({confidence:.2f})")
        
        current_hour = get_hour()
        if 8 <= current_hour < 9:
            late_minute = (datetime.now().hour - 8) * 60 + datetime.now().minute
            save_to_checkin(name, confidence, late_minute)
        elif 17 <= current_hour <= 21:
            save_to_checkout(name, confidence)
        else:
            print("⛔ Ngoài thời gian check-in/check-out hợp lệ!")
        
        color = (0, 255, 0)
    else:
        print("Không tìm thấy nhân viên! Vui lòng thử lại.")
        return
    
    boxes, _ = mtcnn.detect(frame)
    if boxes is not None:
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    cv2.imshow("Recognition Result", frame)
    cv2.waitKey(2000)

if __name__ == "__main__":
    capture_and_recognize()
