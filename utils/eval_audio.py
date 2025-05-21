import numpy as np
import soundfile as sf
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim

def compute_psnr_ssim(original_audio_path, stego_audio_path):
    try:
        # Load audio
        original_audio, sr1 = sf.read(original_audio_path)
        stego_audio, sr2 = sf.read(stego_audio_path)

        if sr1 != sr2:
            raise ValueError("Sample rates do not match.")

        # Potong agar panjang sama
        min_len = min(len(original_audio), len(stego_audio))
        original_audio = original_audio[:min_len]
        stego_audio = stego_audio[:min_len]

        # Normalisasi ke rentang [-1, 1]
        original_audio = original_audio / np.max(np.abs(original_audio))
        stego_audio = stego_audio / np.max(np.abs(stego_audio))

        # Hitung metrik langsung tanpa reshape
        psnr_value = psnr(original_audio, stego_audio, data_range=1.0)
        ssim_value = ssim(original_audio, stego_audio, data_range=1.0, win_size=7, channel_axis=None)

        return psnr_value, ssim_value

    except Exception as e:
        print("[ERROR]", e)
        return None, None

def evaluate_stego_quality():
    original = "assets/stecu_full.wav"
    stego = "audio_out/stego.wav"

    print("[INFO] Evaluating audio imperceptibility...")
    psnr_val, ssim_val = compute_psnr_ssim(original, stego)

    if psnr_val is not None:
        print(f"  PSNR : {psnr_val:.2f} dB (semakin tinggi semakin baik)")
        print(f"  SSIM : {ssim_val:.4f} (mendekati 1 = mirip)")
    else:
        print("[FAILED] Gagal mengevaluasi kualitas audio.")

if __name__ == "__main__":
    evaluate_stego_quality()