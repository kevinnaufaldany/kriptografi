from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def encrypt_image(image_bytes, key=None, iv=None):
    if key is None:
        key = get_random_bytes(16)
    if iv is None:
        iv = get_random_bytes(16)

    cipher = AES.new(key, AES.MODE_CFB, iv=iv)
    ciphertext = cipher.encrypt(image_bytes)
    return ciphertext, key, iv
