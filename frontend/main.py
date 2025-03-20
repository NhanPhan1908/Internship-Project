import sys
from PyQt6.QtWidgets import QApplication
from ui.dashboard import MainWindow  # Import giao diện chính từ thư mục ui

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()  # Khởi tạo cửa sổ chính
    window.show()
    sys.exit(app.exec())  # Chạy ứng dụng
