# antispoof.py
import torch
import cv2
import numpy as np
from torchvision import transforms
from PIL import Image
from model import xception

def preprocess_image(image):
    img = cv2.resize(image, (299, 299))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ])
    return transform(img).unsqueeze(0)

def anti_spoofing(image):
    img_tensor = preprocess_image(image).to("cuda" if torch.cuda.is_available() else "cpu")

    with torch.no_grad():
        output = xception(img_tensor)
        score = torch.sigmoid(output).item()

    return score  # Trả về score thô (0~1)
