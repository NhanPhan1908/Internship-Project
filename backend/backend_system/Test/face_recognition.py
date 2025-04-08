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


DATA_PATH = './data'
os.makedirs(DATA_PATH, exist_ok=True)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)


#database
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
collection_employees = db["employees"]  # Collection of employees, take embedding data from here
collection_attendance = db["attendance"]  # Collection of attendance, save attendance data here

# check GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Init model
mtcnn = MTCNN(keep_all=False, device=device)
facenet = InceptionResnetV1(pretrained="casia-webface").to(device).eval()

# Model Init
def fixed_image_standardization(image_tensor):
    return (image_tensor - 127.5) / 128.0

def trans(img):
    #chuyển đổi ảnh thành tensor và chuẩn hóa
    if isinstance(img, torch.Tensor):
        return img  # Nếu đã là tensor, không cần chuyển đổi
    transform = transforms.Compose([
        transforms.ToTensor(),
        fixed_image_standardization
    ])
    return transform(img)

# load employees embeddings từ MongoDB (collection employees)
def load_embeddings_from_db():
    embeddings = []
    names = []

    for record in collection_employees.find({}, {"name": 1, "embedding": 1, "_id": 0}): #tìm tất cả các bản ghi trong collection employees
          ## Chỉ lấy trường name và embedding, không lấy _id
        names.append(record["name"]) # Lưu tên nhân viên
        embeddings.append(np.array(record["embedding"]))  # Chuyển sang NumPy array vì sẽ dùng cosine similarity
    
    if len(embeddings) == 0:
        return None, None  # Trả về None nếu không có dữ liệu

    return np.array(embeddings), names  # Trả về NumPy array

# save attendance to DB (collection attendance)
def save_to_attendance(name, confidence):
    data = {
        "name": name,
        "confidence": confidence,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    collection_attendance.insert_one(data)
    print(f"Đã lưu vào attendance: {data}")

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
        #box detect
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
    embeddings, names = load_embeddings_from_db()  # Lấy danh sách embedding từ MongoDB

    if embeddings is None:
        print(" Không tìm thấy dữ liệu nhận diện trong MongoDB!") 
        return

    # chuyển frame thành ảnh PIL để sử dụng MTCNN
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # Chuyển đổi từ BGR (OpenCV) sang RGB (PIL)
    face = mtcnn(image)

    if face is None:
        print(" Không phát hiện khuôn mặt! Vui lòng thử lại.")
        return 

   
    is_real = anti_spoofing(frame, anti_spoofing_model)  # 

    if not is_real:
        print("Cảnh báo: Phát hiện giả mạo! Không cho phép nhận diện.")
        return  

    # chuyển tensor thành tensor chuẩn hóa
    face_tensor = trans(face).unsqueeze(0).to(device)  # thêm batch dimension

    # tính embedding mới
    with torch.no_grad():
        new_embedding = facenet(face_tensor).cpu().numpy().flatten()  # Flatten thành vector 1D

    # cosine similarities
    similarities = [1 - cosine(new_embedding, emb.flatten()) for emb in embeddings]  # Flatten embeddings cũ
    best_match = np.argmax(similarities)

    # xác định danh tính
    if similarities[best_match] > 0.3: # ngưỡng nhận diện chính xác
        name = names[best_match]
        confidence = similarities[best_match]
        print(f"✅ Nhận diện thành công: {name} ({confidence:.2f})")
        color = (0, 255, 0)

        # lưu vào database nếu nhận diện thành công
        save_to_attendance(name, confidence)

    else:
        print(" Không tìm thấy nhân viên! Vui lòng thử lại.")
        return  # không lưu vào database và yêu cầu quét lại

    # hiển thị bounding box với tên nhân viên
    boxes, _ = mtcnn.detect(frame)
    if boxes is not None:
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow("Recognition Result", frame)
    cv2.waitKey(2000)


# run code
if __name__ == "__main__":
    capture_and_recognize()
