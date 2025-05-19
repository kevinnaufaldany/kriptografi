import wave
import numpy as np

def embed_echo(audio_path, output_path, data, delay=500, amp=0.6):
    with wave.open(audio_path, 'rb') as audio:
        params = audio.getparams()
        frames = np.frombuffer(audio.readframes(params.nframes), dtype=np.int16)

    bit_data = ''.join(format(byte, '08b') for byte in data)
    modified = frames.copy()

    for i, bit in enumerate(bit_data):
        idx = i * 2 * delay
        if idx + delay < len(modified):
            echo = int(modified[idx] * amp)
            if bit == '1':
                modified[idx + delay] += echo
            else:
                modified[idx + delay] -= echo

    with wave.open(output_path, 'wb') as out:
        out.setparams(params)
        out.writeframes(modified.astype(np.int16).tobytes())
