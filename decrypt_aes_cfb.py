from Crypto.Cipher import AES

def decrypt_image(ciphertext, key, iv):
    cipher = AES.new(key, AES.MODE_CFB, iv=iv)
    return cipher.decrypt(ciphertext)