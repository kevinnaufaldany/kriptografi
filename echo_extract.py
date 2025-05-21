import wave
import numpy as np

def extract_echo(stego_path, bit_count, delay=500, amp=0.6, threshold=5):
    with wave.open(stego_path, 'rb') as audio:
        frames = np.frombuffer(audio.readframes(audio.getnframes()), dtype=np.int16)

    extracted_bits = []
    for i in range(bit_count):
        idx = i * 2 * delay
        if idx + delay < len(frames):
            diff = frames[idx + delay] - frames[idx]
            if diff > threshold:
                extracted_bits.append('1')
            elif diff < -threshold:
                extracted_bits.append('0')
            else:
                extracted_bits.append('0')  # bisa juga 'x' kalau mau abaikan

    byte_data = []
    for i in range(0, len(extracted_bits), 8):
        byte = extracted_bits[i:i+8]
        if len(byte) < 8:
            break
        byte_data.append(int(''.join(byte), 2))
    return bytes(byte_data)
