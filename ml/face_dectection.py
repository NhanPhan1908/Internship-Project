import cv2
from facenet_pytorch import MTCNN
import torch
from datetime import datetime
import os

# GPU/CPU
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# img path saved
IMG_PATH = './data/test_images/'
usr_name = input("Input your name: ")
USR_PATH = os.path.join(IMG_PATH, usr_name)

# Tạo thư mục nếu chưa có
if not os.path.exists(USR_PATH):
    os.makedirs(USR_PATH)

# MTCNN init
mtcnn = MTCNN(margin=20,thresholds= [0.7, 0.7, 0.8], keep_all=False, post_process=False, device=device)

# Camera init
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  #fullHD
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)   #720p

# Imame Setting
count = 50  
leap = 1  

while cap.isOpened() and count:
    isSuccess, frame = cap.read()
    if not isSuccess:
        print("Không thể lấy dữ liệu từ camera")
        break

    # check exist of face
    faces = mtcnn(frame)
    if faces is not None and leap % 2: 
        # create namefile as realtime Ex:2025-3-18_10-24-23
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        path = os.path.join(USR_PATH, f"{timestamp}_{count}.jpg")

        # save image
        mtcnn(frame, save_path=path)
        print(f"Đã lưu ảnh: {path}")
        count -= 1  
        
    leap += 1  
    cv2.imshow('Face Capturing', frame)

    #ESC to cancel
    if cv2.waitKey(1) & 0xFF == 27:
        break

# done
cap.release()
cv2.destroyAllWindows()
print("Chụp ảnh thành công")
