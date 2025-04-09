import sys
import cv2
import requests
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QGroupBox, QTabWidget
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QPixmap, QImage

BACKEND_URL = "http://127.0.0.1:8000/recognize/" 

class FaceRecognitionTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.capture = None
        self.prev_face = None
        self.stable_start_time = None
        self.stability_duration = 2000
        self.timer = None
    
    def initUI(self):
        self.setWindowTitle("Nhận diện khuôn mặt")
        self.setGeometry(100, 100, 900, 600)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        
        # Camera Viewfinder Group
        camera_group = QGroupBox("Camera Feed")
        self.camera_viewfinder = QLabel("Camera Feed")
        self.camera_viewfinder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_viewfinder.setFixedSize(480, 360)
        self.camera_viewfinder.setStyleSheet("border: 1px solid black; background-color: lightgray")
        camera_layout = QVBoxLayout()
        camera_layout.addWidget(self.camera_viewfinder)
        camera_group.setLayout(camera_layout)
        # Recognition Result Group
        recognition_group = QGroupBox("Kết quả nhận diện")
        self.recognition_label = QLabel("Recognition Result")
        self.recognition_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recognition_label.setFixedSize(480, 360)
        self.recognition_label.setStyleSheet("border: 1px solid black; background-color: lightgray")
        recognition_layout = QVBoxLayout()
        recognition_layout.addWidget(self.recognition_label)
        recognition_group.setLayout(recognition_layout)
        
        # Detect Result Group
        detect_group = QGroupBox("Detect Result")
        self.detect_label = QLabel("Detect Result")
        self.detect_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detect_label.setFixedSize(480, 360)
        self.detect_label.setStyleSheet("border: 1px solid black; background-color: lightgray")
        detect_layout = QVBoxLayout()
        detect_layout.addWidget(self.detect_label)
        detect_group.setLayout(detect_layout)
        
        # Employee Data Group
        employee_group = QGroupBox("Employee Data")
        self.employee_data_label = QLabel("Employee Data")
        self.employee_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.employee_data_label.setFixedSize(480, 360)
        self.employee_data_label.setStyleSheet("border: 1px solid black; background-color: lightgray")
        employee_layout = QVBoxLayout()
        employee_layout.addWidget(self.employee_data_label)
        employee_group.setLayout(employee_layout)
        
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
    
    def showEvent(self, event):
        super().showEvent(event)
        if self.capture is None:
            self.log_output.append("Đang mở camera...")
            self.start_camera()
        else:
            self.log_output.append("Camera đã mở.")
    def hideEvent(self, a0):
        self.stop_camera()
        return super().hideEvent(a0)
    
    def start_camera(self):
        if self.capture is not None:
            self.log_output.append("Camera đã được bật rồi!")
            return

        self.capture = cv2.VideoCapture(1)
        
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
        if not ret:
            self.log_output.append("❌ Lỗi khi đọc dữ liệu từ camera.")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        if len(faces) > 0:
            (x, y, w, h) = faces[0]  #lấy khuôn mặt đầu tiên được cho vào camera
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2) # bonding box

        # Hàm kiểm tra độ ổn định, nhận 4 giá trị prev_face, so sánh nếu không thay đổi nhiều <10 thì coi như giữ nguyên vị trí
            if self.prev_face is not None:
                 dx = abs(x - self.prev_face[0])
                 dy = abs(y - self.prev_face[1])
                 dw = abs(w - self.prev_face[2])
                 dh = abs(h - self.prev_face[3])

                 if dx < 40 and dy < 40 and dw < 40 and dh < 40:
                    if self.stable_start_time is None:
                         self.stable_start_time = QTime.currentTime()
                    else:
                         elapsed = self.stable_start_time.msecsTo(QTime.currentTime())
                         if elapsed > self.stability_duration:
                            self.log_output.append("✅ Gương mặt ổn định - tiến hành chụp...")
                            self.capture_and_recognize_face()
                            self.stable_start_time = None  # Reset sau khi chụp
                 else:
                    self.stable_start_time = None  # Di chuyển → reset thời gian
            else:
                self.stable_start_time = QTime.currentTime()
            self.prev_face = (x, y, w, h)
        else:
            self.prev_face = None
            self.stable_start_time = None
        self.display_image(frame, self.camera_viewfinder)

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
                status = result.get("status", "unknown")
                detect = result.get("detect", False)
                recognize = result.get("recognize", False)
                name = result.get("name", "Không rõ")
                confidence = result.get("confidence", "N/A")
                message = result.get("message", "")

                self.log_output.append("📸 Kết quả nhận diện:")
                self.log_output.append(f"🔹 Trạng thái: {status}")
                self.log_output.append(f"🔹 Khuôn mặt phát hiện: {'✅ Có' if detect else '❌ Không'}")
                self.log_output.append(f"🔹 Nhận diện thành công: {'✅ Có' if recognize else '❌ Không'}")
                self.log_output.append(f"🔹 Tên: {name}")
                self.log_output.append(f"🔹 Độ tự tin: {confidence}")
                self.log_output.append(f"💬 Thông báo: {message}")
            else:
                self.log_output.append(f"❌ Lỗi từ server: {response.status_code}")
        except Exception as e:
            self.log_output.append(f"❌ Lỗi kết  ngoài: {repr(e)}")
    
    
    def stop_camera(self):
        if self.capture:
            self.capture.release()
            self.capture = None
            self.log_output.append("❌ Camera đã tắt.")
        if self.timer:
            self.timer.stop()
            self.timer = None
    
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
