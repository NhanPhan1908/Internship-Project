import bcrypt
from Crypto.Cipher import AES
import base64

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def encrypt_data(data: str, key: str):
    cipher = AES.new(key.encode(), AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode())
    return base64.b64encode(cipher.nonce + ciphertext).decode()


def decrypt_data(enc_data: str, key: str):
    enc_data = base64.b64decode(enc_data)
    nonce, ciphertext = enc_data[:16], enc_data[16:]
    cipher = AES.new(key.encode(), AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt(ciphertext).decode()
