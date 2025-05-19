def extract_echo(stego_path, bit_count, delay=500, amp=0.6):
    import wave
    import numpy as np

    with wave.open(stego_path, 'rb') as audio:
        frames = np.frombuffer(audio.readframes(audio.getnframes()), dtype=np.int16)

    extracted_bits = []
    for i in range(bit_count):
        idx = i * 2 * delay
        if idx + delay < len(frames):
            diff = frames[idx + delay] - frames[idx]
            bit = '1' if diff > 0 else '0'
            extracted_bits.append(bit)

    byte_data = []
    for i in range(0, len(extracted_bits), 8):
        byte = extracted_bits[i:i+8]
        byte_data.append(int(''.join(byte), 2))
    return bytes(byte_data)
