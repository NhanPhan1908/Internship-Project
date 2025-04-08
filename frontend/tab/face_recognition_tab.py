import sys
import cv2
import requests
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QGroupBox, QTabWidget
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
        self.setWindowTitle("Nhận diện khuôn mặt")
        self.setGeometry(100, 100, 900, 600)

        # Camera Viewfinder Group
        camera_group = QGroupBox("Camera Feed")
        self.camera_viewfinder = QLabel("Camera Feed")
        self.camera_viewfinder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_viewfinder.setFixedSize(480, 360)
        self.camera_viewfinder.setStyleSheet("border: 1px solid black; background-color: lightgray")

        # Recognition Result Group
        recognition_group = QGroupBox("Kết quả nhận diện")
        self.recognition_label = QLabel("Recognition Result")
        self.recognition_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recognition_label.setFixedSize(480, 360)
        self.recognition_label.setStyleSheet("border: 1px solid black; background-color: lightgray")

        # Detect Result Group
        detect_group = QGroupBox("Detect Result")
        self.detect_label = QLabel("Detect Result")
        self.detect_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detect_label.setFixedSize(480, 360)
        self.detect_label.setStyleSheet("border: 1px solid black; background-color: lightgray")

        # Employee Data Group
        employee_group = QGroupBox("Employee Data")
        self.employee_data_label = QLabel("Employee Data")
        self.employee_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.employee_data_label.setFixedSize(480, 360)
        self.employee_data_label.setStyleSheet("border: 1px solid black; background-color: lightgray")

        # Layout cho Camera Feed, Recognition, Detect và Employee Data (2x2)
        grid_layout = QVBoxLayout()
        
        top_row_layout = QHBoxLayout()
        top_row_layout.addWidget(camera_group)
        top_row_layout.addWidget(recognition_group)

        bottom_row_layout = QHBoxLayout()
        bottom_row_layout.addWidget(detect_group)
        bottom_row_layout.addWidget(employee_group)

        grid_layout.addLayout(top_row_layout)
        grid_layout.addLayout(bottom_row_layout)

        # Button Group (Chức năng)
        button_group = QGroupBox("Chức năng")
        self.start_camera_button = QPushButton("Bật Camera")
        self.start_camera_button.clicked.connect(self.start_camera)
        self.capture_button = QPushButton("Chụp & Nhận diện")
        self.capture_button.clicked.connect(self.capture_and_recognize_face)
        self.capture_button.setEnabled(False)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.start_camera_button)
        button_layout.addWidget(self.capture_button)
        button_group.setLayout(button_layout)

        # Log Output Group
        log_group = QGroupBox("Phản hồi hệ thống")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(120)
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)

        # Layout Tổng
        main_layout = QHBoxLayout()
        
        # Phần camera và nhận diện chiếm 2/3 diện tích
        main_layout.addLayout(grid_layout, 3)
        
        # Phần chức năng chiếm 1/3 diện tích
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        right_layout.addWidget(button_group)
        right_layout.addWidget(log_group)
        
        main_layout.addLayout(right_layout, 1)

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
            response = requests.post("http://localhost:8000/recognize/", files=files)
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
        self.setWindowTitle("Hệ thống nhận diện khuôn mặt")
        self.setGeometry(100, 100, 1400, 800)
        self.initUI()
    
    def initUI(self):
        self.face_recognition_tab = FaceRecognitionTab()
        self.addTab(self.face_recognition_tab, "Nhận diện khuôn mặt")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())
