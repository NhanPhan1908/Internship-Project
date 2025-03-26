import cv2
import torch
import numpy as np
from facenet_pytorch import InceptionResnetV1, MTCNN
from torchvision import transforms
from scipy.spatial.distance import cosine
from PIL import Image
import os

# 📂 Đường dẫn lưu dữ liệu
DATA_PATH = './data'
os.makedirs(DATA_PATH, exist_ok=True)

# 🖥 Kiểm tra GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 🔍 Khởi tạo model
mtcnn = MTCNN(keep_all=False, device=device)
facenet = InceptionResnetV1(pretrained="casia-webface").to(device).eval()

# 📌 Chuẩn hóa ảnh
def fixed_image_standardization(image_tensor):
    return (image_tensor - 127.5) / 128.0

def trans(img):
    transform = transforms.Compose([
        transforms.ToTensor(),
        fixed_image_standardization
    ])
    return transform(img)

# capture and recognize
def capture_and_recognize():
    cap = cv2.VideoCapture(0) # open camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 

    print("Hãy nhìn vào camera. Nhấn 'SPACE' để chụp ảnh, 'ESC' để thoát.")

    while True:
        ret, frame = cap.read() # read frame
        if not ret:
            print("Camera lỗi!")
            break

        # 📌 bounding box when detech
        boxes, _ = mtcnn.detect(frame)  # detect face, call mtcnn
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                # frame, start_point, end_point, color, thickness
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) 
                # frame, text, org, font, fontScale, color, thickness
                cv2.putText(frame, "Detected", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2) 

        cv2.imshow("Capture Face", frame) # display frame
        key = cv2.waitKey(1) & 0xFF # 8 bit

        if key == 32:  # Space
            print("Đang nhận diện...")
            recognize_face(frame)

        elif key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

#  Nhận diện khuôn mặt
def recognize_face(frame):
    try:
        embeddings = torch.load(f"{DATA_PATH}/faceslist.pth") # load embeddings
        names = np.load(f"{DATA_PATH}/usernames.npy") # load names

        if embeddings is None or names is None:
            raise ValueError("Danh sách embeddings trống!")
    except (FileNotFoundError, ValueError):
        print("Không tìm thấy dữ liệu nhận diện!")
        return

    # Chuyển frame thành ảnh PIL
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    face = mtcnn(image)

    if face is None:
        print("Không phát hiện khuôn mặt!")
        cv2.putText(frame, "Không phát hiện khuôn mặt", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow("Recognition Result", frame)
        cv2.waitKey(2000)
        return

    # Tính embedding mới
    with torch.no_grad():
        new_embedding = facenet(trans(face).unsqueeze(0).to(device))

    # So sánh với danh sách đã lưu
    # cosine similarity
    similarities = [1 - cosine(new_embedding.cpu().numpy(), emb.cpu().numpy()) for emb in embeddings]
    
    best_match = np.argmax(similarities) # best match

    # Xác định danh tính
    if similarities[best_match] > 0.5:
        name = names[best_match]
        print(f" Nhận diện thành công: {name}")
        color = (0, 255, 0)
    else:
        name = "Không tìm thấy nhân viên"
        print("❌ Không tìm thấy nhân viên")
        color = (0, 0, 255)

    # 📌 Hiển thị bounding box với tên nhân viên
    boxes, _ = mtcnn.detect(frame)
    if boxes is not None:
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2) # frame, start_point, end_point, color, thickness
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2) # frame, text, org, font, fontScale, color, thickness

    cv2.imshow("Recognition Result", frame)
    cv2.waitKey(2000)

# 📌 Chạy chương trình
if __name__ == "__main__":
    capture_and_recognize()
