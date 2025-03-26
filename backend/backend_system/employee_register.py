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

# 🎯 Kết nối MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["face_recognition"]
collection = db["employees"]

# 🖥 Kiểm tra GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 🔍 Khởi tạo model nhận diện khuôn mặt
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

class EmployeeRegister(EmployeeRegisterUI):
    def __init__(self):
        super().__init__()

        # 🎥 Khởi động camera
        self.cap = cv2.VideoCapture(0)
        self.timer_id = self.startTimer(30)  # update camera 30ms/frame
        self.capture_button.clicked.connect(self.capture_face)  # connect button

    def timerEvent(self, event):
        """ Cập nhật camera lên UI """
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # convert color
            boxes, _ = mtcnn.detect(frame) # detect face
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box) # box = [x1, y1, x2, y2]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) # draw rectangle

            h, w, ch = frame.shape
            qimg = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888) ## convert to QImage
            self.camera_label.setPixmap(QPixmap.fromImage(qimg)) # show camera

    def capture_face(self):
        """ Chụp ảnh, trích xuất embedding & lưu vào database """
        ret, frame = self.cap.read()
        if not ret:
            QMessageBox.critical(self, "Lỗi", "Không thể chụp ảnh từ camera!")
            return

        name = self.input_name.text().strip() # get name
        emp_id = self.input_id.text().strip() # get ID

        if not name or not emp_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập đầy đủ thông tin!")
            return

        #  Recognize face
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        face = mtcnn(image)

        if face is None:
            QMessageBox.warning(self, "Lỗi", "Không phát hiện khuôn mặt!")
            return

        # embedding 
        with torch.no_grad():
            embedding = facenet(trans(face).unsqueeze(0).to(device)).cpu().numpy()

        # check ID
        if collection.find_one({"employee_id": emp_id}):
            QMessageBox.warning(self, "Lỗi", "Mã nhân viên đã tồn tại!")
            return

        # 📌 Lưu vào database
        collection.insert_one({
            "employee_id": emp_id,
            "name": name,
            "embedding": embedding.tolist()
        })

        QMessageBox.information(self, "Thành công", f"Đã đăng ký nhân viên: {name}!")
        self.input_name.clear()
        self.input_id.clear()

    def closeEvent(self, event):
        """ Đóng camera khi thoát ứng dụng """
        self.cap.release()
        event.accept()

# 📌 Chạy ứng dụng
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmployeeRegister()
    window.show()
    sys.exit(app.exec())
