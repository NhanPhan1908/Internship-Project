import glob
import torch
from torchvision import transforms
from facenet_pytorch import InceptionResnetV1
from mtcnn import MTCNN
import os
from PIL import Image
import numpy as np

# path
IMG_PATH = './data/test_images'
DATA_PATH = './data'
os.makedirs(DATA_PATH, exist_ok=True)  # if there is no folder, create

# check GPU
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# standardize image
def fixed_image_standardization(image_tensor):
    return (image_tensor - 127.5) / 128.0

# tranform img
def trans(img):
    transform = transforms.Compose([
        transforms.ToTensor(),
        fixed_image_standardization
    ])
    return transform(img)

# load model
facenet = InceptionResnetV1(
    classify=False,
    pretrained="casia-webface"
).to(device)
facenet.eval()

# Load MTCNN
mtcnn = MTCNN(keep_all=False, device=device)

# Init embedding and employee name
embeddings = []
names = []

#check employee forder
for usr in os.listdir(IMG_PATH):
    embeds = []
    usr_path = os.path.join(IMG_PATH, usr)

    if not os.path.isdir(usr_path):
        continue

    for file in glob.glob(os.path.join(usr_path, '*.jpg')):
        try:
            img = Image.open(file)
        except:
            continue

        # Phát hiện khuôn mặt trong ảnh
        face = mtcnn(img)
        if face is None:
            continue

        # Trích xuất đặc trưng khuôn mặt bằng FaceNet
        with torch.no_grad():
            embedding = facenet(trans(face).unsqueeze(0).to(device))
            embeds.append(embedding)

    if len(embeds) == 0:
        continue

    # Tính trung bình vector embeddings của từng nhân viên
    embedding_avg = torch.cat(embeds).mean(0, keepdim=True)
    embeddings.append(embedding_avg)
    names.append(usr)

# save embeddings and names
embeddings = torch.cat(embeddings)  # [n, 512]
names = np.array(names)

torch.save(embeddings, os.path.join(DATA_PATH, "faceslist.pth"))
np.save(os.path.join(DATA_PATH, "usernames.npy"), names)

print("Lưu gương mặt thành công!")
