import sys
import cv2
import requests
import json
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QTabWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage

BACKEND_URL = "http://127.0.0.1:8000/recognize/" 

class FaceRecognitionTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.capture = None
        self.timer = None
    
    def initUI(self):
        self.camera_viewfinder = QLabel("Camera Feed")
        self.camera_viewfinder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_viewfinder.setFixedSize(480, 360)

        self.recognition_label = QLabel("Recognition Result")
        self.recognition_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recognition_label.setFixedSize(480, 360)

        camera_layout = QHBoxLayout()
        camera_layout.addWidget(self.camera_viewfinder)
        camera_layout.addWidget(self.recognition_label)

        self.start_camera_button = QPushButton("Start Camera")
        self.start_camera_button.clicked.connect(self.start_camera)
        self.capture_button = QPushButton("Capture & Recognize")
        self.capture_button.clicked.connect(self.capture_and_recognize_face)
        self.capture_button.setEnabled(False)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.start_camera_button)
        button_layout.addWidget(self.capture_button)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(120)

        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        top_layout.addLayout(camera_layout, 4)
        top_layout.addLayout(button_layout, 1)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.log_output)

        self.setLayout(main_layout)

    def start_camera(self):
        if self.capture is not None:
            self.log_output.append("⚠️ Camera đã được bật rồi!")
            return

        self.capture = cv2.VideoCapture(0)
        
        if not self.capture.isOpened():
            self.log_output.append("❌ Không thể mở camera. Vui lòng kiểm tra kết nối.")
            self.capture = None
            return
        
        self.log_output.append("📷 Camera đã mở thành công.")
        self.capture_button.setEnabled(True)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        if self.capture is None:
            return

        ret, frame = self.capture.read()
        if ret:
            self.display_image(frame, self.camera_viewfinder)
        else:
            self.log_output.append("❌ Lỗi khi đọc dữ liệu từ camera.")

    def capture_and_recognize_face(self):
        self.log_output.append("🔄 Đang gửi ảnh đến backend...")

        if self.capture is None:
            self.log_output.append("❌ Camera chưa được mở.")
            return

        ret, frame = self.capture.read()
        if not ret:
            self.log_output.append("❌ Không thể chụp ảnh từ camera.")
            return

        _, img_encoded = cv2.imencode(".jpg", frame)
        files = {"file": ("face.jpg", img_encoded.tobytes(), "image/jpeg")}

        try:
            response = requests.post(BACKEND_URL, files=files)
            if response.status_code == 200:
                result = response.json()
                self.log_output.append(f"✅ {result['message']}")
            else:
                self.log_output.append(f"❌ Lỗi từ server: {response.status_code}")
        except Exception as e:
            self.log_output.append(f"❌ Lỗi kết nối: {str(e)}")
    
    def display_image(self, img, label):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width, channel = img_rgb.shape
        bytes_per_line = 3 * width
        qt_img = QPixmap.fromImage(QImage(img_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888))
        label.setPixmap(qt_img.scaled(label.width(), label.height(), Qt.AspectRatioMode.KeepAspectRatio))

    def closeEvent(self, event):
        if self.capture:
            self.capture.release()

class MainApp(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition System")
        self.setGeometry(100, 100, 1400, 800)
        self.initUI()
    
    def initUI(self):
        self.face_recognition_tab = FaceRecognitionTab()
        self.addTab(self.face_recognition_tab, "Face Recognition")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())
