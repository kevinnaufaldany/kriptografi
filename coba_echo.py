import numpy as np
import wave
import os

# === Parameter Echo Hiding ===
DELAY_0 = 100     # Delay untuk bit 0
DELAY_1 = 300     # Delay untuk bit 1
AMP     = 0.6     # Amplitudo echo
WINDOW  = 20      # Ukuran window energi (untuk ekstraksi)
GAP     = 2000    # Jarak antar bit (dalam sample)

def read_wave(filename):
    with wave.open(filename, 'rb') as wf:
        params = wf.getparams()
        frames = wf.readframes(params.nframes)
        samples = np.frombuffer(frames, dtype=np.int16)
        print(params)
        print(f"[INFO] Total samples: {len(samples)}")
    return samples, params

def write_wave(filename, samples, params):
    with wave.open(filename, 'wb') as wf:
        wf.setparams(params)
        wf.writeframes(samples.astype(np.int16).tobytes())

def embed_echo(samples, data_bits, delay0=DELAY_0, delay1=DELAY_1, amp=AMP):
    stego = samples.copy().astype(np.float32)
    for i, bit in enumerate(data_bits):
        delay = delay1 if bit == 1 else delay0
        start = i * GAP
        if start + delay + 1 >= len(stego):
            print(f"[WARNING] Bit ke-{i} tidak cukup ruang, berhenti embed.")
            break
        stego[start + delay] += amp * stego[start]
    return np.clip(stego, -32768, 32767).astype(np.int16)

def extract_echo(samples, total_bits, delay0=DELAY_0, delay1=DELAY_1, amp=AMP, window=WINDOW):
    recovered_bits = []
    for i in range(total_bits):
        start = i * GAP
        if start + delay1 + window >= len(samples):
            print(f"[WARNING] Bit ke-{i} tidak cukup untuk ekstraksi, berhenti.")
            break
        energy0 = np.sum(np.square(samples[start + delay0 : start + delay0 + window]))
        energy1 = np.sum(np.square(samples[start + delay1 : start + delay1 + window]))
        bit = 1 if energy1 > energy0 else 0
        recovered_bits.append(bit)
    return recovered_bits

# ===== MAIN =====
if __name__ == '__main__':
    # Create dummy file with parameters
    dummy_samples = np.zeros(2 * 44100, dtype=np.int16)
    dummy_params = wave.WavParamsWritable(nchannels=1, sampwidth=2, framerate=44100, nframes=len(dummy_samples), comptype='NONE', compname='not compressed')
    write_wave("dummy.wav", dummy_samples, dummy_params)
    
    bits_to_hide = [1, 0, 1, 1, 0, 1, 0, 0, 1]
    print("[INPUT DATA]:", bits_to_hide)
    
    input_audio = 'dummy.wav'   # ganti dengan audio kamu
    stego_audio = 'stego.wav'

    if not os.path.exists(input_audio):
        raise FileNotFoundError(f"File '{input_audio}' tidak ditemukan. Siapkan file WAV mono 16-bit!")

    samples, params = read_wave(input_audio)

    # Sisipkan bit
    stego_samples = embed_echo(samples, bits_to_hide)
    write_wave(stego_audio, stego_samples, params)
    print("[INFO] Data berhasil disisipkan ke:", stego_audio)

    # Ekstraksi
    extracted_bits = extract_echo(stego_samples, len(bits_to_hide))
    print("[EXTRACTED DATA]:", extracted_bits)

    # Evaluasi
    correct = sum([a == b for a, b in zip(bits_to_hide, extracted_bits)])
    print(f"[ACCURACY]: {correct}/{len(bits_to_hide)} benar ({100*correct/len(bits_to_hide):.1f}%)")
