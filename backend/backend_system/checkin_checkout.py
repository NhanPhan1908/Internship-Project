from fastapi import FastAPI, File, UploadFile
import cv2
import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from facenet_pytorch import InceptionResnetV1, MTCNN
from scipy.spatial.distance import cosine
import pymongo
from datetime import datetime
import io

app = FastAPI()

# Kết nối MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
collection_employees = db["employees"]

# Load model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(keep_all=False, device=device)
facenet = InceptionResnetV1(pretrained="casia-webface").to(device).eval()

# Tải embeddings từ database
def load_embeddings_from_db():
    embeddings, names = [], []
    for record in collection_employees.find({}, {"name": 1, "embedding": 1}):
        if "embedding" not in record:
            continue
        names.append(record["name"])
        embeddings.append(np.array(record["embedding"]))
    return (np.array(embeddings), names) if embeddings else (None, None)

# Lấy thời gian hiện tại
def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Nhận diện khuôn mặt
def recognize_face(image: np.array):
    embeddings, names = load_embeddings_from_db()
    if embeddings is None:
        return {"message": "Không tìm thấy dữ liệu nhận diện!"}
    if names is None:
        return {"message": "Không tìm thấy tên nhân viên!"}
    # Convert ảnh từ OpenCV (BGR) sang PIL (RGB)
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    # Phát hiện khuôn mặt
    face = mtcnn(pil_img)  
    if face is None:
        return {"message": "Không phát hiện khuôn mặt!"}

    # Đảm bảo ảnh đúng kích thước đầu vào
    face = face.unsqueeze(0).to(device)  # Add batch dimension

    # Tính toán embedding
    with torch.no_grad():
        new_embedding = facenet(face).cpu().numpy().flatten()

    # So sánh với database
    similarities = [1 - cosine(new_embedding, emb.flatten()) for emb in embeddings]
    best_match = np.argmax(similarities)

    if similarities[best_match] > 0.3:
        name, confidence = names[best_match], similarities[best_match]
        return {"name": name, "confidence": confidence}
    else:
        return {"message": "Không tìm thấy nhân viên!"}

# API nhận diện
@app.post("/recognize/")
async def recognize(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    result = recognize_face(image)
    return result

# Chạy server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
