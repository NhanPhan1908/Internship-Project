import torch
import cv2
import timm
import numpy as np
from torchvision import transforms
from PIL import Image
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

def load_anti_spoofing_model(model_name="xception"):
    """
    Load pre-trained anti-spoofing model from timm.
    """
    model = timm.create_model(model_name, pretrained=True, num_classes=1)
    model.eval()
    return model

def preprocess_image(frame):
    """
    Convert OpenCV frame to tensor for model inference.
    """
    img = cv2.resize(frame, (299, 299))  # Resize ảnh về kích thước chuẩn của Xception
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Chuyển sang RGB
    img = Image.fromarray(img)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])  # Chuẩn hóa dữ liệu
    ])
    return transform(img).unsqueeze(0)  # Thêm batch dimension

def anti_spoofing(frame, model):
    """
    Perform anti-spoofing detection.
    Returns True if the face is real, False if it's fake.
    """
    img_tensor = preprocess_image(frame)
    
    with torch.no_grad():
        output = model(img_tensor)
        score = torch.sigmoid(output).item()  # Convert output to probability
    
    print(f"🎭 Anti-spoofing Score: {score:.2f}")
    return score >= 0.3  # Nếu score < 0.5 thì ảnh bị coi là giả mạo

# Load model khi khởi động
anti_spoofing_model = load_anti_spoofing_model()

# Ví dụ sử dụng:
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        result = anti_spoofing(frame, anti_spoofing_model)
        print("Real Face" if result else "Fake Face")

        cv2.imshow("Anti-Spoofing", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # Nhấn ESC để thoát
            break
    
    cap.release()
    cv2.destroyAllWindows()
