import wave
import numpy as np
import os

# === RSA Manual (Lightweight) ===

def power(base, expo, m):
    res = 1
    base = base % m
    while expo > 0:
        if expo & 1:
            res = (res * base) % m
        base = (base * base) % m
        expo = expo // 2
    return res

def modInverse(e, phi):
    for d in range(2, phi):
        if (e * d) % phi == 1:
            return d
    return -1

def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

def generateKeys():
    p = 61
    q = 53
    n = p * q        # 3233
    phi = (p - 1) * (q - 1)
    e = 17           # umum digunakan
    d = modInverse(e, phi)
    return e, d, n

def encrypt(m, e, n):
    return power(m, e, n)

def decrypt(c, d, n):
    return power(c, d, n)

# === Echo Hiding Improved ===

def embed_bit_echo(signal, bit, delay=500, attenuation=0.7):
    output = np.copy(signal)
    if bit == '1':
        echo = np.zeros_like(signal)
        echo[delay:] = attenuation * signal[:-delay]
        output += echo
    return output

def extract_bit_echo(signal, delay=500, threshold=0.15):
    if len(signal) <= delay:
        return '0'
    corr = np.correlate(signal[delay:], signal[:-delay], mode='valid')
    energy = np.sum(signal ** 2)
    if energy == 0:
        return '0'
    similarity = np.max(corr) / energy
    return '1' if similarity > threshold else '0'

# === Main Embedding & Extraction ===

# Generate RSA keys
e, d, n = generateKeys()

# Message: 1 character
message = "a"
m_ascii = ord(message)
cipher = encrypt(m_ascii, e, n)
print(f"[INFO] Original: '{message}' (ASCII: {m_ascii}) -> Encrypted: {cipher}")

# Convert to 12-bit bitstream
bitstream = format(cipher, '012b')
print(f"[INFO] Bitstream (12-bit): {bitstream}")

# Load mono WAV
wav_path = "stecu_full.wav"         # Ganti sesuai file Anda
output_path = "echo_embedded.wav"

with wave.open(wav_path, 'rb') as wav:
    params = wav.getparams()
    frames = wav.readframes(params.nframes)
    signal = np.frombuffer(frames, dtype=np.int16)

# Normalize to [-1.0, 1.0]
signal = signal.astype(np.float32)
signal /= np.max(np.abs(signal))

# Embed bits
embedded_signal = np.copy(signal)
start = 1000
bit_chunk = 8000

print("[INFO] Embedding bits...")
for i, bit in enumerate(bitstream):
    idx = start + i * bit_chunk
    if idx + bit_chunk > len(embedded_signal):
        print("[ERROR] Audio too short.")
        break
    chunk = signal[idx:idx+bit_chunk]
    embedded_chunk = embed_bit_echo(chunk, bit)
    embedded_signal[idx:idx+bit_chunk] = embedded_chunk

    extracted_bit = extract_bit_echo(embedded_chunk)
    print(f"Bit {i}: Embed '{bit}' -> Extracted '{extracted_bit}' - {'✓' if bit == extracted_bit else '✗'}")

# Denormalize before saving
embedded_signal = np.clip(embedded_signal, -1.0, 1.0)
embedded_signal = (embedded_signal * 32767).astype(np.int16)

with wave.open(output_path, 'wb') as wav:
    wav.setparams(params)
    wav.writeframes(embedded_signal.tobytes())

# Extract
print("\n[INFO] Extracting bits...")
with wave.open(output_path, 'rb') as wav:
    extracted = np.frombuffer(wav.readframes(params.nframes), dtype=np.int16)
extracted = extracted.astype(np.float32) / 32767

extracted_bits = ""
for i in range(len(bitstream)):
    idx = start + i * bit_chunk
    if idx + bit_chunk > len(extracted):
        break
    bit = extract_bit_echo(extracted[idx:idx+bit_chunk])
    extracted_bits += bit
    print(f"Bit {i}: Expected '{bitstream[i]}', Got '{bit}' - {'✓' if bitstream[i] == bit else '✗'}")

try:
    recovered_cipher = int(extracted_bits, 2)
    decrypted_ascii = decrypt(recovered_cipher, d, n)
    recovered_message = chr(decrypted_ascii) if 32 <= decrypted_ascii <= 126 else '?'
    print(f"\n[RESULT] Extracted Bits:  {extracted_bits}")
    print(f"[RESULT] Decrypted ASCII: {decrypted_ascii} -> '{recovered_message}'")
except ValueError as e:
    print(f"\n[ERROR] Failed to convert or decrypt: {e}")
