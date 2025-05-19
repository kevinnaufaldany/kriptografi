import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import io
import wave
import contextlib
import numpy as np
import matplotlib.pyplot as plt
import encrypt_aes_cfb
import decrypt_aes_cfb
import echo_hiding
import echo_extract

class KriptoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AES-CFB + Echo Hiding GUI")
        self.root.geometry("900x700")

        # Widgets
        tk.Label(root, text="Embed setiap N sample (default 2):").pack()
        self.embed_entry = tk.Entry(root)
        self.embed_entry.insert(0, "2")
        self.embed_entry.pack(pady=5)
        tk.Button(root, text="Pilih Gambar", command=self.load_image, width=30).pack(pady=5)
        tk.Button(root, text="Pilih Audio", command=self.load_audio, width=30).pack(pady=5)
        tk.Button(root, text="Proses Enkripsi + Sisip", command=self.process, width=30).pack(pady=5)
        tk.Button(root, text="Preview Waveform Audio", command=self.plot_waveform, width=30).pack(pady=5)
        tk.Button(root, text="Ekstrak + Dekripsi dari Stego", command=self.extract_decrypt, width=30).pack(pady=5)

        self.status_label = tk.Label(root, text="", fg="blue", wraplength=800, justify="left")
        self.status_label.pack(pady=10)

        self.image_label = tk.Label(root)
        self.image_label.pack(pady=5)

        self.image_path = None
        self.audio_path = None
        self.ciphertext = None
        self.aes_key = None
        self.aes_iv = None
        self.min_duration_required = None

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png"), ("All files", "*.*")])
        if path:
            self.image_path = path
            img = Image.open(path).convert("RGB")
            img_resized = img.resize((100, 100))
            tk_img = ImageTk.PhotoImage(img_resized)
            self.image_label.configure(image=tk_img)
            self.image_label.image = tk_img

            # Enkripsi gambar
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_data = img_bytes.getvalue()
            self.ciphertext, self.aes_key, self.aes_iv = encrypt_aes_cfb.encrypt_image(img_data)

            bit_count = len(self.ciphertext) * 8
            embed_every_n_sample = int(self.embed_entry.get())
            sample_rate = 44100
            total_samples = bit_count * embed_every_n_sample
            self.min_duration_required = total_samples / sample_rate

            self.status_label.config(
                text=(
                    f"Gambar: {path.split('/')[-1]}\n"
                    f"Ukuran gambar: {img.size}, Ukuran ciphertext: {len(self.ciphertext)} byte ({bit_count} bit)\n"
                    f"Min durasi audio: {self.min_duration_required:.2f} detik "
                    f"(dengan embed tiap {embed_every_n_sample} sample)"
                )
            )

    def load_audio(self):
        path = filedialog.askopenfilename(filetypes=[("WAV", "*.wav")])
        if path:
            try:
                with contextlib.closing(wave.open(path, 'rb')) as audio:
                    nchannels = audio.getnchannels()
                    framerate = audio.getframerate()
                    frames = audio.getnframes()
                    duration = frames / float(framerate)

                    if nchannels != 1:
                        raise ValueError("Audio harus mono.")
                    if framerate != 44100:
                        raise ValueError("Sampling rate harus 44.1 kHz.")
                    if self.min_duration_required and duration < self.min_duration_required:
                        raise ValueError(
                            f"Durasi audio {duration:.2f}s kurang dari {self.min_duration_required:.2f}s yang dibutuhkan."
                        )

                self.audio_path = path
                self.status_label.config(
                    text=self.status_label.cget("text") + "\n\n"
                    f"Audio: {path.split('/')[-1]}\nChannel: {nchannels}, Sample Rate: {framerate}, Durasi: {duration:.2f} detik"
                )
                messagebox.showinfo("Audio Valid", "Audio memenuhi syarat.")

            except Exception as e:
                messagebox.showerror("Audio tidak valid", str(e))

    def process(self):
        if not self.image_path or not self.audio_path:
            messagebox.showerror("Error", "Pilih gambar dan audio terlebih dahulu.")
            return

        output_audio = filedialog.asksaveasfilename(defaultextension=".wav")
        if not output_audio:
            return

        embed_every_n_sample = int(self.embed_entry.get())
        length_prefix = len(self.ciphertext).to_bytes(4, byteorder='big')
        data_with_length = length_prefix + self.ciphertext
        echo_hiding.embed_echo(self.audio_path, output_audio, data_with_length, delay=embed_every_n_sample)
        echo_hiding.embed_echo(self.audio_path, "preview_stego.wav", self.ciphertext, delay=embed_every_n_sample)

        with open("key.bin", "wb") as f:
            f.write(self.aes_key)
        with open("iv.bin", "wb") as f:
            f.write(self.aes_iv)

        messagebox.showinfo("Sukses", f"Stego-audio disimpan di {output_audio}.\nKey dan IV disimpan ke key.bin & iv.bin.")

    def plot_waveform(self):
        if not self.audio_path:
            messagebox.showerror("Error", "Pilih audio terlebih dahulu!")
            return

        with wave.open(self.audio_path, 'rb') as wf:
            n_frames = wf.getnframes()
            original_data = wf.readframes(n_frames)
            original_array = np.frombuffer(original_data, dtype=np.int16)

        try:
            with wave.open("preview_stego.wav", 'rb') as wf2:
                n_frames2 = wf2.getnframes()
                stego_data = wf2.readframes(n_frames2)
                stego_array = np.frombuffer(stego_data, dtype=np.int16)
        except:
            stego_array = None

        plt.figure(figsize=(10, 4))
        plt.subplot(2, 1, 1)
        plt.plot(original_array, linewidth=0.5)
        plt.title("Original Audio")

        if stego_array is not None:
            plt.subplot(2, 1, 2)
            plt.plot(stego_array, color='red', linewidth=0.5)
            plt.title("Stego Audio")

        plt.tight_layout()
        plt.show()

    def extract_decrypt(self):
        stego_path = filedialog.askopenfilename(filetypes=[("WAV", "*.wav")])
        if not stego_path:
            return

        try:
            with open("key.bin", "rb") as f:
                k = f.read()
            with open("iv.bin", "rb") as f:
                v = f.read()
        except:
            messagebox.showerror("Gagal", "key.bin atau iv.bin tidak ditemukan.")
            return

        extracted = echo_extract.extract_echo(stego_path, bit_count=120000)
        cipher_len = int.from_bytes(extracted[:4], byteorder='big')
        ciphertext = extracted[4:4+cipher_len]
        plaintext = decrypt_aes_cfb.decrypt_image(ciphertext, k, v)

        out_path = filedialog.asksaveasfilename(defaultextension=".png")
        if out_path:
            with open(out_path, "wb") as f:
                f.write(plaintext)
            messagebox.showinfo("Sukses", f"Gambar berhasil disimpan di:\n{out_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KriptoGUI(root)
    root.mainloop()
