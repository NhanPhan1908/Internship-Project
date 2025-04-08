import sys
import cv2
import numpy as np
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QLineEdit, QMessageBox, QTextEdit, QGroupBox
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer


BACKEND_URL = "http://127.0.0.1:8000/register/"

class EmployeeRegisterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cap = None  # Camera
        self.image = None  # Ảnh chụp
        self.timer = QTimer(self)  # Timer để cập nhật camera
        self.timer.timeout.connect(self.update_frame)

    def initUI(self):
        self.setWindowTitle("Đăng ký Nhân viên")
        self.setGeometry(100, 100, 900, 600)

        # Camera Group
        camera_group = QGroupBox("Camera & Ảnh Chụp")
        self.camera_label = QLabel(self)
        self.camera_label.setFixedSize(400, 300)
        self.camera_label.setStyleSheet("border: 1px solid black; background-color: lightgray;")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.face_picture = QLabel(self)
        self.face_picture.setFixedSize(400, 300)
        self.face_picture.setStyleSheet("border: 1px solid black; background-color: lightgray;")
        self.face_picture.setAlignment(Qt.AlignmentFlag.AlignCenter)

        camera_layout = QHBoxLayout()
        camera_layout.addWidget(self.camera_label)
        camera_layout.addWidget(self.face_picture)
        camera_group.setLayout(camera_layout)

        # Form Group
        form_group = QGroupBox("Thông Tin Nhân Viên")
        self.input_name = QLineEdit(self)
        self.input_name.setPlaceholderText("Nhập tên nhân viên")
        self.input_id = QLineEdit(self)
        self.input_id.setPlaceholderText("Nhập mã nhân viên")
        self.input_address = QLineEdit(self)
        self.input_address.setPlaceholderText("Nhập địa chỉ")
        self.input_department = QLineEdit(self)
        self.input_department.setPlaceholderText("Nhập phòng ban")
        self.input_position = QLineEdit(self)
        self.input_position.setPlaceholderText("Nhập chức vụ")
        self.input_mail = QLineEdit(self)
        self.input_mail.setPlaceholderText("Nhập mail")
        self.input_phone = QLineEdit(self)
        self.input_phone.setPlaceholderText("Nhập số điện thoại")

        form_layout = QVBoxLayout()
        for widget in [self.input_name, self.input_id, self.input_address, 
                       self.input_department, self.input_position, 
                       self.input_mail, self.input_phone]:
            form_layout.addWidget(widget)
        form_group.setLayout(form_layout)

        # Button Group
        button_group = QGroupBox("Chức Năng")
        self.start_button = QPushButton("Bật Camera", self)
        self.capture_button = QPushButton("Chụp Ảnh", self)
        self.save_button = QPushButton("Lưu Dữ Liệu", self)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.save_button)
        button_group.setLayout(button_layout)

        # Log Group
        log_group = QGroupBox("Phản hồi từ hệ thống")
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Phản hồi từ hệ thống...")

        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)

        # Right Layout
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)  
        right_layout.setSpacing(0)  
        right_layout.addWidget(form_group)
        right_layout.addWidget(button_group)

        # Main Layout
        main_top_layout = QHBoxLayout()
        main_top_layout.addWidget(camera_group, 2)
        main_top_layout.addLayout(right_layout, 1)

        main_layout = QVBoxLayout()
        main_layout.addLayout(main_top_layout)
        main_layout.addWidget(log_group)

        self.setLayout(main_layout)

        # Kết nối sự kiện
        self.start_button.clicked.connect(self.start_camera)
        self.capture_button.clicked.connect(self.capture_image)
        self.save_button.clicked.connect(self.save_data)

    def start_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(1)
            if not self.cap.isOpened():
                QMessageBox.critical(self, "Lỗi", "Không thể mở camera!")
                return
            self.timer.start(30)  

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                qimg = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
                self.camera_label.setPixmap(QPixmap.fromImage(qimg))

    def capture_image(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                self.image = frame.copy()
                self.face_picture.setPixmap(QPixmap.fromImage(self.convert_cv_qt(frame)))
                self.log_output.append("Ảnh đã chụp thành công!")
            else:
                self.log_output.append("Lỗi: Không thể chụp ảnh!")

    def convert_cv_qt(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        return QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)

    def save_data(self):
        name = self.input_name.text().strip()
        emp_id = self.input_id.text().strip()
        address = self.input_address.text().strip()
        department = self.input_department.text().strip()
        position = self.input_position.text().strip()
        email = self.input_mail.text().strip()
        phone = self.input_phone.text().strip()

        if not name or not emp_id:
            self.log_output.append("⚠️ Cảnh báo: Vui lòng nhập đầy đủ thông tin!")
            return

        if self.image is None:
            self.log_output.append("⚠️ Cảnh báo: Vui lòng chụp ảnh trước khi lưu!")
            return

    # Encode ảnh thành định dạng JPEG
        success, buffer = cv2.imencode('.jpg', self.image)
        if not success:
            self.log_output.append("❌ Không thể chuyển ảnh!")
            return

        files = {
            "image": ("face.jpg", buffer.tobytes(), "image/jpeg")}

        data = {
            "employee_id": emp_id,
            "name": name,
            "address": address,
            "department": department,
            "position": position,
            "email": email,
            "phone": phone,
        }
        
        try:
            response = requests.post(BACKEND_URL, files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == 1:
                    self.log_output.append(f"✅ {result['message']}")
                else:
                    self.log_output.append(f"❌ {result['message']}")
            else:
                self.log_output.append(f"❌ Lỗi từ server: {response.status_code}") 
        except requests.exceptions.RequestException as e:
            self.log_output.append(f"❌ Lỗi kết nối: {str(e)}")
        


    def closeEvent(self, event):
        if self.cap:
            self.timer.stop()
            self.cap.release()
            self.cap = None
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmployeeRegisterTab()
    window.show()
    sys.exit(app.exec())
