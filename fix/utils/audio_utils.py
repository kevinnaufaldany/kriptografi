import soundfile as sf
import os

def load_audio(file_path):
    audio, sr = sf.read(file_path)
    return audio, sr

def save_audio(file_path, audio_data, sr):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    sf.write(file_path, audio_data, sr)
