import torch
from facenet_pytorch import InceptionResnetV1, MTCNN

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Khởi tạo model
mtcnn = MTCNN(keep_all=False, device=device)
facenet = InceptionResnetV1(pretrained="casia-webface").to(device).eval()
