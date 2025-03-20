import cv2
import torch
import numpy as np
from facenet_pytorch import InceptionResnetV1, MTCNN
from torchvision import transforms
from scipy.spatial.distance import cosine
from PIL import Image

#path
DATA_PATH = './data'

# Load face list
try:
    embeddings = torch.load(f"{DATA_PATH}/faceslist.pth")
    names = np.load(f"{DATA_PATH}/usernames.npy")
    print("Face embeddings & names loaded successfully!")
except:
    print("Error: No face embeddings found. Run face_list.py first!")
    exit()

# GPU/CPU
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

# Load model detect
mtcnn = MTCNN(keep_all=False, device=device)

# Load model facenet
facenet = InceptionResnetV1(pretrained="casia-webface").to(device)
facenet.eval()

# standardization
def fixed_image_standardization(image_tensor):
    return (image_tensor - 127.5) / 128.0

def trans(img):
    transform = transforms.Compose([
        transforms.ToTensor(),
        fixed_image_standardization
    ])
    return transform(img)

# open camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("🎥 Camera started. Press 'Esc' to exit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Camera error!")
        break

    face = mtcnn(frame)
    if face is not None:
        with torch.no_grad():
            new_embedding = facenet(trans(face).unsqueeze(0).to(device))

        # Tính độ tương đồng Cosine
        similarities = [1 - cosine(new_embedding.cpu().numpy(), emb.cpu().numpy()) for emb in embeddings]
        best_match = np.argmax(similarities)
        
        if similarities[best_match] > 0.5:  
            name = names[best_match]
            color = (0, 255, 0)
        else:
            name = "Unknown"
            color = (0, 0, 255)

        # display results
        cv2.putText(frame, name, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)

    cv2.imshow('Face Recognition', frame)

    # esc to out
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
