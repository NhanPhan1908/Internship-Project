import cv2
import torch
import pymongo
import numpy as np
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QImage, QPixmap
from facenet_pytorch import InceptionResnetV1, MTCNN
from torchvision import transforms
from PIL import Image
import sys
from ui_employee_register import EmployeeRegisterUI  # Import UI

# 🎯 Connect MongoDB
try:
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["Intern"]
    collection = db["employees"]
    print("[INFO] Kết nối MongoDB thành công!")
except Exception as e:
    print(f"[ERROR] Không thể kết nối MongoDB: {e}")
    sys.exit(1)

# 🖥 Check GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"[INFO] Đang sử dụng: {'GPU' if torch.cuda.is_available() else 'CPU'}")

# Init Model
try:
    mtcnn = MTCNN(keep_all=False, device=device)
    facenet = InceptionResnetV1(pretrained="casia-webface").to(device).eval()
    print("[INFO] Model nhận diện khuôn mặt đã tải thành công!")
except Exception as e:
    print(f"[ERROR] Lỗi tải model: {e}")
    sys.exit(1)

# 📌 Standardization
def fixed_image_standardization(image_tensor):
    return (image_tensor - 127.5) / 128.0 # chuẩn hóa về 127.5

def trans(img):
    transform = transforms.Compose([
        transforms.ToTensor(),
        fixed_image_standardization
    ])
    return transform(img)

class EmployeeRegister(EmployeeRegisterUI):
    def __init__(self):
        super().__init__()

        # Start camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Lỗi", "Không thể mở camera!")
            print("[ERROR] Không thể mở camera!")
            sys.exit(1)

        self.timer_id = self.startTimer(30)  # update camera 30ms/frame
        self.capture_button.clicked.connect(self.capture_face)  # connect button

    def timerEvent(self, event):
        """ Cập nhật camera lên UI """
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Chuyển đổi màu
            boxes, _ = mtcnn.detect(frame)  # Phát hiện khuôn mặt
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box)  # Lấy tọa độ khuôn mặt
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Vẽ khung

            h, w, ch = frame.shape
            # Convert to QImage
            qimg = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888) #(frame.data, width, heigh, bytesPerLine, format)
            self.camera_label.setPixmap(QPixmap.fromImage(qimg))  # Hiển thị camera

    def capture_face(self):
        """ Chụp ảnh, trích xuất embedding & lưu vào database """
        ret, frame = self.cap.read() # Lấy ảnh từ camera
        ## Nếu không lấy được ảnh, hiển thị thông báo lỗi
        if not ret:
            QMessageBox.critical(self, "Lỗi", "Không thể chụp ảnh từ camera!")
            print("[ERROR] Không thể chụp ảnh từ camera!")
            return

        name = self.input_name.text().strip()  # Lấy tên
        emp_id = self.input_id.text().strip()  # Lấy ID nhân viên

        if not name or not emp_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập đầy đủ thông tin!")
            print("[WARNING] Thiếu thông tin nhân viên!")
            return

        print(f"[INFO] Đang xử lý nhận diện khuôn mặt cho nhân viên: {name} (ID: {emp_id})")

        # Chuyển ảnh từ OpenCV sang PIL
        # Nếu không chuyển đổi, sẽ không thể sử dụng MTCNN để phát hiện khuôn mặt
        # Chuyển đổi từ BGR (OpenCV) sang RGB (PIL)
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # 🟢 Detect face và lấy khuôn mặt đã cắt
        face = mtcnn(image)

        if face is None:
            QMessageBox.warning(self, "Lỗi", "Không phát hiện khuôn mặt!")
            print("[ERROR] Không phát hiện khuôn mặt!")
            return

        print("[INFO] Đã phát hiện khuôn mặt, trích xuất embedding...")

        try:
            # 🟢 CHUYỂN face từ Tensor ➝ NumPy ndarray (cần cho Facenet)
            face = face.permute(1, 2, 0).numpy()  # Chuyển từ (C, H, W) → (H, W, C)
    
            # Chuẩn hóa và trích xuất embedding
            face = trans(face)  # Chuyển thành Tensor chuẩn hóa
            face = face.unsqueeze(0).to(device)  # Thêm batch dimension
            with torch.no_grad():
                embedding = facenet(face).cpu().numpy()

            print(f"[INFO] Embedding shape: {embedding.shape}")
        except Exception as e:
            print(f"[ERROR] Lỗi trích xuất embedding: {e}")
            QMessageBox.critical(self, "Lỗi", "Lỗi khi trích xuất đặc trưng khuôn mặt!")
            return

        # Kiểm tra ID nhân viên
        existing_employee = collection.find_one({"employee_id": emp_id})
        if existing_employee:
            QMessageBox.warning(self, "Lỗi", "Mã nhân viên đã tồn tại!")
            print("[ERROR] Mã nhân viên đã tồn tại trong DB!")
            return

        # 📌 Lưu vào database
        employee_data = {
            "employee_id": emp_id,
            "name": name,
            "embedding": embedding.tolist()
        }

        try:
            result = collection.insert_one(employee_data)
            if result.inserted_id:
                print(f"[SUCCESS] Đã lưu vào MongoDB với ID: {result.inserted_id}")
                QMessageBox.information(self, "Thành công", f"Đã đăng ký nhân viên: {name}!")
            else:
                print("[ERROR] Không thể lưu vào MongoDB!")
        except Exception as e:
            print(f"[ERROR] Không thể lưu vào MongoDB: {e}")
            QMessageBox.critical(self, "Lỗi", "Lỗi khi lưu dữ liệu vào MongoDB!")

        self.input_name.clear()
        self.input_id.clear()

    def closeEvent(self, event):
        """ Đóng camera khi thoát ứng dụng """
        self.cap.release()
        print("[INFO] Camera đã đóng!")
        event.accept()

# 📌 Chạy ứng dụng
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmployeeRegister()
    window.show()
    print("[INFO] Ứng dụng đã khởi động!")
    sys.exit(app.exec())
