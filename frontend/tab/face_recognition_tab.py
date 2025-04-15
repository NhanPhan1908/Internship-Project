import sys
import cv2
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QGroupBox, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QLayout
from .camera_thread import CameraThread

BACKEND_URL = "http://127.0.0.1:8000/recognize/"

class FaceRecognitionTab(QWidget):
    def __init__(self):
        super().__init__()
        self.capture_thread = None
        self.capture = None
        self.last_frame = None
        self.prev_face = None
        self.stable_start_time = None
        self.stability_duration = 2000  # ms
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Nhận diện khuôn mặt")
        self.setGeometry(100, 100, 900, 600)

        # UI components
        self.camera_viewfinder = self.create_display_label("Camera Feed")
        self.recognition_label = self.create_display_label("Recognition Result")
        self.detect_label = self.create_display_label("Detect Result")
        self.employee_data_label = self.create_display_label("Employee Data")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(120)

        # Buttons
        self.start_camera_button = QPushButton("Bật Camera")
        self.start_camera_button.clicked.connect(self.start_camera)

        self.capture_button = QPushButton("Chụp & Nhận diện")
        self.capture_button.clicked.connect(self.capture_and_recognize_face)
        self.capture_button.setEnabled(False)

        # Layouts
        grid_layout = QVBoxLayout()
        top_row = QHBoxLayout()
        bottom_row = QHBoxLayout()

        top_row.addWidget(self.wrap_group("Camera Feed", self.camera_viewfinder))
        top_row.addWidget(self.wrap_group("Kết quả nhận diện", self.recognition_label))
        bottom_row.addWidget(self.wrap_group("Detect Result", self.detect_label))
        bottom_row.addWidget(self.wrap_group("Employee Data", self.employee_data_label))
        grid_layout.addLayout(top_row)
        grid_layout.addLayout(bottom_row)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.start_camera_button)
        button_layout.addWidget(self.capture_button)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.wrap_group("Chức năng", button_layout))
        right_layout.addWidget(self.wrap_group("Phản hồi hệ thống", self.log_output))

        main_layout = QHBoxLayout()
        main_layout.addLayout(grid_layout, 3)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)

    def create_display_label(self, text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedSize(480, 360)
        label.setStyleSheet("border: 1px solid black; background-color: lightgray")
        return label

    def wrap_group(self, title, content):
        group = QGroupBox(title)
        layout = QVBoxLayout()
        if isinstance(content, QLayout):
            layout.addLayout(content)
        else:
            layout.addWidget(content)
        group.setLayout(layout)
        return group

    def showEvent(self, event):
        super().showEvent(event)
        self.log_output.append("Đang mở camera...")
        self.start_camera()

    def start_camera(self):
        if self.capture_thread and self.capture_thread.isRunning():
            self.log_output.append("📷 Camera đã bật.")
            return

        self.capture_thread = CameraThread()
        self.capture = self.capture_thread.capture
        self.capture_thread.frame_ready.connect(self.update_frame)
        self.capture_thread.running = True
        self.capture_thread.start()
        self.capture_button.setEnabled(True)
        self.log_output.append("✅ Camera khởi động thành công.")

    def stop_camera(self):
        if self.capture_thread and self.capture_thread.isRunning():
            self.capture_thread.stop()
            self.capture_thread = None
            self.log_output.append("🛑 Camera đã dừng.")

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

    def update_frame(self, frame):
        if frame is None:
            return

        self.last_frame = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if self.prev_face:
                dx, dy, dw, dh = [abs(a - b) for a, b in zip((x, y, w, h), self.prev_face)]
                if dx < 40 and dy < 40 and dw < 40 and dh < 40:
                    if not self.stable_start_time:
                        self.stable_start_time = QTime.currentTime()
                    else:
                        elapsed = self.stable_start_time.msecsTo(QTime.currentTime())
                        if elapsed > self.stability_duration:
                            self.log_output.append("✅ Gương mặt ổn định - tiến hành chụp...")
                            self.capture_and_recognize_face()
                            self.stable_start_time = None
                else:
                    self.stable_start_time = None
            else:
                self.stable_start_time = QTime.currentTime()
            self.prev_face = (x, y, w, h)
        else:
            self.prev_face = None
            self.stable_start_time = None

        self.display_image(frame, self.camera_viewfinder)

    def capture_and_recognize_face(self):
        if self.capture is None:
            self.log_output.append("❌ Camera chưa được mở.")
            return
        if self.last_frame is None:
            self.log_output.append("❌ Không có ảnh để nhận diện.")
            return

        ret, frame = self.capture.read()
        if not ret:
            self.log_output.append("❌ Không thể chụp ảnh từ camera.")
            return

        self.log_output.append("🔄 Đang gửi ảnh đến backend...")
        _, img_encoded = cv2.imencode(".jpg", frame)
        files = {"file": ("face.jpg", img_encoded.tobytes(), "image/jpeg")}

        try:
            response = requests.post(BACKEND_URL, files=files)
            if response.status_code == 200:
                data = response.json()
                self.display_recognition_result(data)
            else:
                self.log_output.append(f"❌ Lỗi server: {response.status_code}")
        except Exception as e:
            self.log_output.append(f"❌ Lỗi gửi ảnh: {repr(e)}")

    def display_recognition_result(self, result):
        self.log_output.append("📸 Kết quả nhận diện:")
        self.log_output.append(f"🔹 Trạng thái: {result.get('status', 'unknown')}")
        self.log_output.append(f"🔹 Phát hiện: {'✅ Có' if result.get('detect') else '❌ Không'}")
        self.log_output.append(f"🔹 Nhận diện: {'✅ Có' if result.get('recognize') else '❌ Không'}")
        self.log_output.append(f"🔹 Tên: {result.get('name', 'Không rõ')}")
        self.log_output.append(f" employee_id: {result.get('employee_id', 'N/A')}")
        self.log_output.append(f"🔹 Độ tự tin: {result.get('confidence', 'N/A')}")
        self.log_output.append(f"💬 {result.get('message', '')}")

    def display_image(self, img, label):
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb_image.shape
        bytes_per_line = 3 * width
        qt_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(qt_image).scaled(label.width(), label.height(), Qt.AspectRatioMode.KeepAspectRatio))
