import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Khóa AES 256-bit (32 bytes)
AES_KEY = b"Nhandepzai"  # Thay bằng khóa bí mật của bạn
AES_IV = b"Nhandepzai"  # IV (Initialization Vector)

# Mã hóa Embedding Vector
def encrypt_embedding(embedding_vector):
    embedding_str = json.dumps(embedding_vector)  # Chuyển về chuỗi JSON
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    encrypted_bytes = cipher.encrypt(pad(embedding_str.encode(), AES.block_size))
    return base64.b64encode(encrypted_bytes).decode()  # Chuyển sang base64 để lưu trữ

# Giải mã Embedding Vector
def decrypt_embedding(encrypted_embedding):
    encrypted_bytes = base64.b64decode(encrypted_embedding)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
    return json.loads(decrypted_bytes.decode())  # Chuyển về danh sách số thực
