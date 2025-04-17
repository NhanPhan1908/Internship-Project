from PyQt6.QtCore import QThread, pyqtSignal
import requests
import cv2


BACKEND_URL = "http://127.0.0.1:8000/recognize/"

class RecognitionThread(QThread):
    result_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, frame):
        super().__init__()
        self.frame = frame

    def run(self):
        try:
            _, img_encoded = cv2.imencode(".jpg", self.frame)
            files = {"file": ("face.jpg", img_encoded.tobytes(), "image/jpeg")}
            response = requests.post(BACKEND_URL, files=files)
            if response.status_code == 200:
                result = response.json()
                self.result_ready.emit(result)
            else:
                self.error.emit(f"Lỗi server: {response.status_code}")
        except Exception as e:
            self.error.emit(f"Lỗi gửi ảnh: {repr(e)}")
