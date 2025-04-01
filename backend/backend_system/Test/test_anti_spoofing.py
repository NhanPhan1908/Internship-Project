import cv2
import anti_spoofing  # Giả sử bạn đã định nghĩa hàm này trong file anti_spoofing.py
def test_anti_spoofing():
    """
    Chạy camera để kiểm tra chức năng chống giả mạo.
    Nhấn 'SPACE' để kiểm tra ảnh, 'ESC' để thoát.
    """
    cap = cv2.VideoCapture(0)  # Mở camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Hãy nhìn vào camera. Nhấn 'SPACE' để kiểm tra, 'ESC' để thoát.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("🚫 Lỗi camera!")
            break

        cv2.imshow("Anti-Spoofing Test", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # Nhấn SPACE để kiểm tra
            print("🔍 Đang kiểm tra chống giả mạo...")
            result = anti_spoofing(frame)
            if result:
                print("✅ Người thật!")
            else:
                print("🚫 Phát hiện giả mạo!")
        
        elif key == 27:  # Nhấn ESC để thoát
            break

    cap.release()
    cv2.destroyAllWindows()

# 📌 Gọi hàm test
test_anti_spoofing()
