import cv2

def test_camera():
    # Mở camera (0 là camera mặc định)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Không thể mở camera.")
        return

    print("✅ Camera đang hoạt động. Nhấn 'q' để thoát.")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("⚠️ Không thể đọc frame từ camera.")
            break

        # Chuyển sang ảnh xám
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Hiển thị khung hình
        cv2.imshow('Camera - Nhấn q để thoát', gray)

        # Nhấn 'q' để thoát
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Giải phóng và đóng cửa sổ
    cap.release()
    cv2.destroyAllWindows()
    print("🔒 Camera đã tắt.")

if __name__ == "__main__":
    test_camera()
