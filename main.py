import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
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
import shutil
import os

class KriptoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AES + Echo Hiding")
        self.root.geometry("1000x750")
        self.root.configure(bg="#e9edf0")

        self.image_path = None
        self.audio_path = None
        self.ciphertext = None
        self.aes_key = None
        self.aes_iv = None
        self.min_duration_required = None
        self.total_embed_bits = None

        self.setup_ui()

    def setup_ui(self):
        header = tk.Label(self.root, text="AES Encryption + Echo Hiding", font=("Segoe UI", 18, "bold"), bg="#e9edf0", fg="#2c3e50")
        header.pack(pady=15)

        top_frame = tk.Frame(self.root, bg="#e9edf0")
        top_frame.pack(pady=10, padx=20, fill="x")

        # Label Gambar
        tk.Label(top_frame, text="Gambar", font=("Segoe UI", 11, "bold"), bg="#e9edf0").pack(side="left", padx=(80, 10))
        # Label Audio
        tk.Label(top_frame, text="Audio", font=("Segoe UI", 11, "bold"), bg="#e9edf0").pack(side="right", padx=(10, 80))

        content_frame = tk.Frame(self.root, bg="#e9edf0")
        content_frame.pack(pady=5, padx=20, fill="x")

        self.image_box = self.create_drop_area(content_frame, "Drop atau pilih gambar (.png)", self.load_image)
        self.image_box.pack(side="left", expand=True, padx=10, fill="both")

        self.audio_box = self.create_drop_area(content_frame, "Drop atau pilih audio (.wav)", self.load_audio)
        self.audio_box.pack(side="right", expand=True, padx=10, fill="both")

        self.image_info_label = tk.Label(self.image_box, text="", bg="#ffffff", fg="#2c3e50", font=("Segoe UI", 9))
        self.image_info_label.pack(pady=5)

        self.audio_info_label = tk.Label(self.audio_box, text="", bg="#ffffff", fg="#2c3e50", font=("Segoe UI", 9))
        self.audio_info_label.pack(pady=5)

        param_frame = tk.Frame(self.root, bg="#e9edf0")
        param_frame.pack(pady=10)
        tk.Label(param_frame, text="Embed setiap N sample (default 2):", bg="#e9edf0", font=("Segoe UI", 10)).pack()
        self.embed_entry = tk.Entry(param_frame, width=10, justify='center')
        self.embed_entry.insert(0, "2")
        self.embed_entry.pack(pady=5)

        action_frame = tk.Frame(self.root, bg="#e9edf0")
        action_frame.pack(pady=15, padx=20, fill="x")

        self.add_column(action_frame, "Enkripsi & Sisipkan", self.process)
        self.add_column(action_frame, "Preview Waveform", self.plot_waveform)
        self.add_column(action_frame, "Ekstrak & Dekripsi", self.extract_decrypt)

        self.status_label = tk.Label(self.root, text="", bg="#e9edf0", fg="#34495e", wraplength=900, justify="left")
        self.status_label.pack(pady=10)

    def create_drop_area(self, parent, text, callback):
        frame = tk.Frame(parent, bg="#ffffff", bd=2, relief="groove", height=180, width=200)
        frame.pack_propagate(False)

        label = tk.Label(frame, text=text, bg="#ffffff", fg="#666666")
        label.pack(expand=True)

        def drop(event):
            filepath = event.data.strip('{').strip('}')
            if os.path.isfile(filepath):
                callback(filepath)

        frame.drop_target_register(DND_FILES)
        frame.dnd_bind('<<Drop>>', drop)

        def on_click(event):
            if 'gambar' in text.lower():
                self.load_image()
            else:
                self.load_audio()

        frame.bind("<Button-1>", on_click)
        return frame

    def add_column(self, parent, title, action):
        col = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        col.pack(side="left", expand=True, padx=10, fill="both")

        label = tk.Label(col, text=title, bg="#ffffff", font=("Segoe UI", 11, "bold"))
        label.pack(pady=10)

        btn = tk.Button(col, text="Preview", command=action, bg="#3498db", fg="white", width=20, relief="raised")
        btn.pack(pady=10)

    def load_image(self, path=None):
        if not path:
            path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if path:
            self.image_path = path
            img = Image.open(path).convert("RGB")
            img_resized = img.resize((120, 120))
            tk_img = ImageTk.PhotoImage(img_resized)
            self.image_box.children['!label'].configure(image=tk_img, text="")
            self.image_box.children['!label'].image = tk_img

            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_data = img_bytes.getvalue()
            self.ciphertext, self.aes_key, self.aes_iv = encrypt_aes_cfb.encrypt_image(img_data)

            length_prefix = len(self.ciphertext).to_bytes(4, byteorder='big')
            data_with_length = length_prefix + self.ciphertext
            self.total_embed_bits = len(data_with_length) * 8

            embed_every_n_sample = int(self.embed_entry.get())
            sample_rate = 44100
            total_samples = self.total_embed_bits * embed_every_n_sample
            self.min_duration_required = total_samples / sample_rate

            self.image_info_label.config(text=(
                f"Gambar: {os.path.basename(path)}\nUkuran ciphertext: {len(self.ciphertext)} byte\nTotal bit: {self.total_embed_bits} bit"))

    def load_audio(self, path=None):
        if not path:
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
                        raise ValueError("Sample rate harus 44.1kHz.")
                    if self.min_duration_required and duration < self.min_duration_required:
                        raise ValueError(f"Durasi audio {duration:.2f}s kurang dari {self.min_duration_required:.2f}s.")

                self.audio_path = path
                self.audio_info_label.config(text=(
                    f"Min durasi audio: {self.min_duration_required:.2f} detik\nAudio: {os.path.basename(path)} ({duration:.2f} detik)"))

                messagebox.showinfo("Audio Valid", "Audio memenuhi syarat.")
            except Exception as e:
                messagebox.showerror("Audio tidak valid", str(e))

    def process(self):
        if not self.image_path or not self.audio_path:
            messagebox.showerror("Error", "Pilih gambar dan audio dulu.")
            return

        output_audio = filedialog.asksaveasfilename(defaultextension=".wav")
        if not output_audio:
            return

        embed_every_n_sample = int(self.embed_entry.get())
        data_with_length = len(self.ciphertext).to_bytes(4, 'big') + self.ciphertext

        echo_hiding.embed_echo(self.audio_path, output_audio, data_with_length, delay=embed_every_n_sample)
        shutil.copy(output_audio, "preview_stego.wav")

        with open("key.bin", "wb") as f:
            f.write(self.aes_key)
        with open("iv.bin", "wb") as f:
            f.write(self.aes_iv)

        messagebox.showinfo("Sukses", f"Stego-audio disimpan: {output_audio}")

    def plot_waveform(self):
        if not self.audio_path:
            messagebox.showerror("Error", "Pilih audio dulu!")
            return

        with wave.open(self.audio_path, 'rb') as wf:
            n_frames = wf.getnframes()
            original_data = wf.readframes(n_frames)
            original_array = np.frombuffer(original_data, dtype=np.int16)

        try:
            with wave.open("preview_stego.wav", 'rb') as wf2:
                stego_data = wf2.readframes(wf2.getnframes())
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

        extracted = echo_extract.extract_echo(stego_path, bit_count=1000000)
        cipher_len = int.from_bytes(extracted[:4], 'big')
        ciphertext = extracted[4:4 + cipher_len]
        plaintext = decrypt_aes_cfb.decrypt_image(ciphertext, k, v)

        out_path = filedialog.asksaveasfilename(defaultextension=".png")
        if out_path:
            with open(out_path, "wb") as f:
                f.write(plaintext)
            messagebox.showinfo("Sukses", f"Gambar disimpan: {out_path}")

if __name__ == '__main__':
    root = TkinterDnD.Tk()
    app = KriptoGUI(root)
    root.mainloop()