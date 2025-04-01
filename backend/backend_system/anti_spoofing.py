import torch
import cv2
import timm # Thư viện timm để tải model anti_spoof
import numpy as np
from torchvision import transforms
from PIL import Image
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# sư dụng timm để tải model chống giả mạo
def load_anti_spoofing_model(model_name="xception"):
    model = timm.create_model(model_name, pretrained=True, num_classes=1) # tải model với pretrained weights
    model.eval() #  chuyển model sang chế độ eval, eval là chế độ không cập nhật weights
    return model

def preprocess_image(frame):
    img = cv2.resize(frame, (299, 299))  # resize ảnh 
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # chuyển sang RGB
    img = Image.fromarray(img)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])  # chuẩn hóa dữ liệu
    ])
    return transform(img).unsqueeze(0)  # thêm batch dimension

def anti_spoofing(frame, model):
    img_tensor = preprocess_image(frame)
    
    with torch.no_grad():
        output = model(img_tensor)
        score = torch.sigmoid(output).item()  # Convert output to probability
    
    print(f" Anti-spoofing Score: {score:.2f}")
    return score >= 0.3  # If < 0.3, it's considered fake

# load model 
anti_spoofing_model = load_anti_spoofing_model()


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
