import wave
import numpy as np

# === RSA Manual (Sederhana untuk 5-bit) ===

def power(base, expo, m):
    res = 1
    base = base % m
    while expo > 0:
        if expo & 1:
            res = (res * base) % m
        base = (base * base) % m
        expo //= 2
    return res

def modInverse(e, phi):
    for d in range(2, phi):
        if (e * d) % phi == 1:
            return d
    return -1

def generateKeys():
    p, q = 11, 13   # kecil agar cipher tetap dalam 5-bit
    n = p * q       # 143
    phi = (p - 1) * (q - 1)  # 120
    e = 7           # kecil dan umum
    d = modInverse(e, phi)
    return e, d, n

def encrypt(m, e, n):
    return power(m, e, n)

def decrypt(c, d, n):
    return power(c, d, n)

# === Echo Hiding (Sinyal Float Normalized) ===

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

# === Helper ===

def char_to_int(ch):
    return ord(ch) - ord('a')

def int_to_char(val):
    return chr(val + ord('a'))

# === Main ===

e, d, n = generateKeys()
message = 'g'

m_val = char_to_int(message)  # 'g' → 6
cipher = encrypt(m_val, e, n)
bitstream = format(cipher, '05b')

print(f"[INFO] Message: '{message}' (val: {m_val}) -> Encrypted: {cipher} -> Bitstream: {bitstream}")

# === Audio Load & Normalize ===

wav_path = "stecu_full.wav"
output_path = "echo_5bit.wav"

with wave.open(wav_path, 'rb') as wav:
    params = wav.getparams()
    frames = wav.readframes(params.nframes)
    signal = np.frombuffer(frames, dtype=np.int16)

signal = signal.astype(np.float32)
signal /= np.max(np.abs(signal))

# === Embed 5-bit ===

embedded_signal = np.copy(signal)
start = 1000
bit_chunk = 8000

for i, bit in enumerate(bitstream):
    idx = start + i * bit_chunk
    if idx + bit_chunk > len(signal):
        print("[ERROR] Audio too short")
        break
    chunk = signal[idx:idx+bit_chunk]
    embedded_chunk = embed_bit_echo(chunk, bit)
    embedded_signal[idx:idx+bit_chunk] = embedded_chunk

# Save
embedded_signal = np.clip(embedded_signal, -1.0, 1.0)
embedded_signal = (embedded_signal * 32767).astype(np.int16)

with wave.open(output_path, 'wb') as wav:
    wav.setparams(params)
    wav.writeframes(embedded_signal.tobytes())

# === Extraction ===

print("\n[INFO] Extracting...")
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
    print(f"Bit {i}: {bitstream[i]} -> {bit} {'✓' if bitstream[i] == bit else '✗'}")

# === Decode
try:
    recovered_cipher = int(extracted_bits, 2)
    recovered_val = decrypt(recovered_cipher, d, n)
    recovered_char = int_to_char(recovered_val) if 0 <= recovered_val < 26 else '?'
    print(f"\n[RESULT] Bits: {extracted_bits}")
    print(f"[RESULT] Cipher: {recovered_cipher} -> Decrypted: {recovered_val} -> '{recovered_char}'")
except Exception as e:
    print(f"[ERROR] Failed to decode: {e}")
