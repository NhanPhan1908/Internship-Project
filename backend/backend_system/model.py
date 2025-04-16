import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
import timm

# Kiểm tra thiết bị
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Khởi tạo các mô hình
mtcnn = MTCNN(keep_all=False, device=device)  # phát hiện khuôn mặt
facenet = InceptionResnetV1(pretrained="casia-webface").to(device).eval()  # trích đặc trưng khuôn mặt
xception = timm.create_model('legacy_xception', pretrained=True, num_classes=1).to(device).eval()  # anti-spoofing
xception.eval()
xception = xception.to(device)
