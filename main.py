import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import io
import wave
import contextlib
import encrypt_aes_cfb
import echo_hiding

class KriptoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AES-CFB + Echo Hiding Steganography")
        self.root.geometry("640x300")

        tk.Button(root, text="Pilih Gambar", command=self.load_image, width=30).pack(pady=10)
        tk.Button(root, text="Pilih Audio", command=self.load_audio, width=30).pack(pady=10)
        tk.Button(root, text="Proses Enkripsi + Sisip", command=self.process, width=30).pack(pady=10)

        self.image_path = None
        self.audio_path = None

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png"), ("All files", "*.*")])
        if path:
            self.image_path = path
            messagebox.showinfo("Gambar Dipilih", f"{path}\n\nSilakan pilih file audio:\n- .wav\n- Mono\n- 44.1kHz\n- Durasi minimal beberapa detik.")

    def load_audio(self):
        path = filedialog.askopenfilename(filetypes=[("WAV", "*.wav")])
        if path:
            try:
                # Load audio properties
                with contextlib.closing(wave.open(path, 'rb')) as audio:
                    nchannels = audio.getnchannels()
                    framerate = audio.getframerate()
                    frames = audio.getnframes()
                    duration = frames / float(framerate)

                    if nchannels != 1:
                        raise ValueError("Audio harus mono.")
                    if framerate != 44100:
                        raise ValueError("Sampling rate harus 44.1 kHz.")

                # Hitung durasi minimal berdasarkan ukuran ciphertext
                if not self.image_path:
                    raise ValueError("Pilih gambar terlebih dahulu untuk menghitung kebutuhan audio.")

                # Hitung ciphertext (sementara tanpa simpan)
                from PIL import Image
                import io
                img = Image.open(self.image_path).resize((100, 100)).convert("RGB")
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_data = img_bytes.getvalue()

                ciphertext, _, _ = encrypt_aes_cfb.encrypt_image(img_data)
                bit_count = len(ciphertext) * 8
                embed_every_n_sample = 2  # 1 bit setiap 2 sample (misal)

                total_sample_needed = bit_count * embed_every_n_sample
                min_duration_required = total_sample_needed / framerate

                if duration < min_duration_required:
                    raise ValueError(
                        f"Durasi audio terlalu pendek.\n"
                        f"Ciphertext = {len(ciphertext)} byte = {bit_count} bit\n"
                        f"Butuh ≥ {min_duration_required:.2f} detik, tapi audio hanya {duration:.2f} detik."
                    )

            except Exception as e:
                messagebox.showerror("Audio tidak valid", str(e))
                return

            self.audio_path = path
            messagebox.showinfo("Audio Dipilih", f"{path}\n✓ Valid dan cukup panjang untuk disisipi.")

    def process(self):
        if not self.image_path or not self.audio_path:
            messagebox.showerror("Error", "Gambar dan audio harus dipilih!")
            return

        img = Image.open(self.image_path).resize((100, 100)).convert("RGB")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()

        ciphertext, key, iv = encrypt_aes_cfb.encrypt_image(img_data)
        output_audio = filedialog.asksaveasfilename(defaultextension=".wav")

        echo_hiding.embed_echo(self.audio_path, output_audio, ciphertext)
        messagebox.showinfo("Sukses", f"Stego audio disimpan di:\n{output_audio}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KriptoGUI(root)
    root.mainloop()
