import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QPixmap
from camera_thread import CameraThread  # Import từ file bạn đã có

class CameraViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 Test CameraThread")

        # Tạo label để hiển thị frame từ webcam
        self.image_label = QLabel("Đang khởi động camera...")
        self.image_label.setScaledContents(True)

        # Layout đơn giản
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # Khởi tạo và chạy CameraThread
        self.camera_thread = CameraThread()
        self.camera_thread.frame_ready.connect(self.update_image)
        self.camera_thread.start()

    def update_image(self, qt_image):
        pixmap = QPixmap.fromImage(qt_image)
        self.image_label.setPixmap(pixmap)

    def closeEvent(self, event):
        # Dừng camera khi đóng cửa sổ
        self.camera_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = CameraViewer()
    viewer.resize(640, 480)
    viewer.show()
    sys.exit(app.exec())
