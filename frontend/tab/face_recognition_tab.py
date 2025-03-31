from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
import cv2
import torch
import numpy as np
from facenet_pytorch import InceptionResnetV1, MTCNN
import pymongo
from torchvision import transforms

# Kết nối MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["attendance_system"]
employees_collection = db["employees"]

# Model nhận diện
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
mtcnn = MTCNN(keep_all=False, device=device)
facenet = InceptionResnetV1(pretrained="casia-webface").eval().to(device)

def trans(img):
    return transforms.Compose([
        transforms.ToTensor(),
        lambda x: (x - 127.5) / 128.0
    ])(img)

class FaceRecognitionTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.image_label = QLabel("Camera Feed")
        layout.addWidget(self.image_label)

        self.capture_button = QPushButton("Capture Face")
        self.capture_button.clicked.connect(self.capture_face)
        layout.addWidget(self.capture_button)

        self.result_label = QLabel("")
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def capture_face(self):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            self.result_label.setText("❌ Camera error!")
            return

        face = mtcnn(frame)
        if face is None:
            self.result_label.setText("🚫 No face detected!")
            return

        employees = list(employees_collection.find({}))
        if not employees:
            self.result_label.setText("🚫 No employees found!")
            return

        with torch.no_grad():
            embedding = facenet(trans(face).unsqueeze(0).to(device)).cpu().numpy()

        best_match = None
        best_similarity = 0.0
        for emp in employees:
            stored_embedding = np.array(emp["embedding"])
            similarity = np.dot(embedding, stored_embedding.T)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = emp

        if best_similarity > 0.5:
            self.result_label.setText(f"✅ Employee: {best_match['name']} (ID: {best_match['employee_id']})")
        else:
            self.result_label.setText("🚫 Employee not found!")
