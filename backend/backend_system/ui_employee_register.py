from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit

class EmployeeRegisterUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Đăng Ký Nhân Viên")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        # 📌 Nhập thông tin nhân viên
        self.label_name = QLabel("Tên Nhân Viên:")
        self.input_name = QLineEdit()
        self.label_id = QLabel("Mã Nhân Viên:")
        self.input_id = QLineEdit()

        # 🎥 Hiển thị camera
        self.camera_label = QLabel("Camera")
        self.capture_button = QPushButton("📸 Chụp ảnh & Đăng ký")

        # 📌 Thêm vào layout
        self.layout.addWidget(self.label_name)
        self.layout.addWidget(self.input_name)
        self.layout.addWidget(self.label_id)
        self.layout.addWidget(self.input_id)
        self.layout.addWidget(self.camera_label)
        self.layout.addWidget(self.capture_button)
        self.setLayout(self.layout)
