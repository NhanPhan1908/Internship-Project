import sys
import cv2
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage

class OpenCVQtDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.capture = None
        self.timer = None
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Camera Viewfinder
        self.camera_viewfinder = QLabel("Camera Feed")
        self.camera_viewfinder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_viewfinder.setFixedSize(640, 480)
        
        # Start Camera Button
        self.start_button = QPushButton("Start Camera")
        self.start_button.clicked.connect(self.start_camera)
        
        # Stop Camera Button
        self.stop_button = QPushButton("Stop Camera")
        self.stop_button.clicked.connect(self.stop_camera)
        
        layout.addWidget(self.camera_viewfinder)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        
        self.setLayout(layout)
    
    def start_camera(self):
        self.capture = cv2.VideoCapture(0)
        
        if not self.capture.isOpened():
            self.camera_viewfinder.setText("❌ Không thể mở camera")
            self.capture = None
            return
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        if self.capture is None:
            return

        ret, frame = self.capture.read()
        if ret:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = img_rgb.shape
            bytes_per_line = 3 * width
            qt_img = QPixmap.fromImage(QImage(img_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888))
            self.camera_viewfinder.setPixmap(qt_img.scaled(self.camera_viewfinder.width(), self.camera_viewfinder.height(), Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.camera_viewfinder.setText("❌ Lỗi đọc dữ liệu camera")
    
    def stop_camera(self):
        if self.timer:
            self.timer.stop()
        if self.capture:
            self.capture.release()
            self.capture = None
        self.camera_viewfinder.setText("📷 Camera đã dừng")
    
    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = OpenCVQtDemo()
    main_window.setWindowTitle("OpenCV with Qt6 Demo")
    main_window.show()
    sys.exit(app.exec())
