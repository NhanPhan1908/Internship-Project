import socket
import json
from face_verification import process_image


HOST = "0.0.0.0"
PORT = 5050
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

def handle_client(client_socket):
    """Xử lý yêu cầu từ client"""
    data = json.loads(client_socket.recv(4096).decode("utf-8"))
    
    if data["action"] == "attendance":
        response = process_image(data["image"], data["employee_id"])
    else:
        response = {"status": "error", "message": "Yêu cầu không hợp lệ"}

    client_socket.send(json.dumps(response).encode("utf-8"))
    client_socket.close()

print("Server đang chạy...")
while True:
    client_socket, _ = server_socket.accept()
    handle_client(client_socket)
