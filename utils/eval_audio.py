import numpy as np
import soundfile as sf
from skimage.metrics import peak_signal_noise_ratio as psnr, structural_similarity as ssim

def compute_psnr_ssim(original_audio_path, stego_audio_path):
    try:
        original_audio, sr1 = sf.read(original_audio_path)
        stego_audio, sr2 = sf.read(stego_audio_path)

        min_len = min(len(original_audio), len(stego_audio))
        original_audio = original_audio[:min_len]
        stego_audio = stego_audio[:min_len]

        original_audio = original_audio / np.max(np.abs(original_audio))
        stego_audio = stego_audio / np.max(np.abs(stego_audio))

        # Convert to 2D
        original_audio_2d = original_audio.reshape(1, -1)
        stego_audio_2d = stego_audio.reshape(1, -1)

        psnr_value = psnr(original_audio_2d, stego_audio_2d, data_range=1.0)
        ssim_value = ssim(original_audio_2d, stego_audio_2d, data_range=1.0)

        return psnr_value, ssim_value
    except Exception as e:
        return str(e), None
