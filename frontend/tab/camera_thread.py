# camera_thread.py
from PyQt6.QtCore import QThread, pyqtSignal
import cv2
from PyQt6.QtGui import QImage, QPixmap
class CameraThread(QThread):
    frame_ready = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.capture = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        if not self.capture.isOpened():
            print("⚠️ Không thể mở webcam.")
            return
        else :
            print("🎥 Webcam đã mở.")
        self.running = False
        self.should_stop_camera = False

    def run(self):
        self.running = True
        while self.running:
            ret, frame = self.capture.read()
            if ret:
                self.frame_ready.emit(frame)  # emit frame gốc (numpy array)
            else:
                print("⚠️ Không thể đọc frame từ webcam.")
    
    def stop(self):
        self.running = False
        self.quit()
        self.wait()
        if self.capture and self.capture.isOpened():
            self.capture.release()
    
