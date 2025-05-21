import tkinter as tk
from tkinter import filedialog, messagebox
import wave
import numpy as np
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import os

class RSAGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RSA + Echo Hiding Debug GUI")
        self.root.geometry("800x600")

        self.audio_path = None
        self.rsa_key = RSA.generate(2048)
        self.public_key = self.rsa_key.publickey()
        
        tk.Label(root, text="Masukkan Teks:").pack()
        self.text_entry = tk.Text(root, height=4, width=60)
        self.text_entry.pack()

        tk.Button(root, text="Pilih Audio WAV", command=self.load_audio).pack(pady=5)
        tk.Button(root, text="Enkripsi & Sisipkan", command=self.encrypt_and_embed).pack(pady=5)
        tk.Button(root, text="Ekstrak & Dekripsi", command=self.extract_and_decrypt).pack(pady=5)

        self.result_box = tk.Text(root, height=6, width=60)
        self.result_box.pack()

    def load_audio(self):
        self.audio_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if self.audio_path:
            print(f"[INFO] Audio dipilih: {self.audio_path}")
            messagebox.showinfo("Info", f"Audio dipilih: {self.audio_path}")

    def encrypt_and_embed(self):
        text = self.text_entry.get("1.0", tk.END).strip()
        if not self.audio_path or not text:
            messagebox.showerror("Error", "Pastikan audio dan teks telah diisi.")
            return

        try:
            cipher = PKCS1_OAEP.new(self.public_key)
            encrypted = cipher.encrypt(text.encode())
            bitstream = ''.join(format(byte, '08b') for byte in encrypted)
            bit_len = len(bitstream)
            header = format(bit_len, '016b')
            bitstream = header + bitstream

            print(f"[DEBUG] Panjang ciphertext: {len(encrypted)} bytes")
            print(f"[DEBUG] Panjang bitstream total: {len(bitstream)} bits")

            with wave.open(self.audio_path, 'rb') as wave_read:
                params = wave_read.getparams()
                frames = np.frombuffer(wave_read.readframes(wave_read.getnframes()), dtype=np.int16)

            if len(bitstream) * 100 > len(frames):
                messagebox.showerror("Error", "Audio tidak cukup panjang untuk menyisipkan pesan.")
                return

            modified = frames.copy()
            safe_limit = 32000  # untuk menghindari overflow int16

            for i, bit in enumerate(bitstream):
                idx = i * 100
                if abs(modified[idx]) > safe_limit:
                    print(f"[WARN] Sample {idx} terlalu besar, dilewati")
                    continue
                if bit == '1':
                    modified[idx] = min(32767, modified[idx] + 500)
                else:
                    modified[idx] = max(-32768, modified[idx] - 500)

            output_path = "embedded_output.wav"
            with wave.open(output_path, 'wb') as wave_write:
                wave_write.setparams(params)
                wave_write.writeframes(modified.astype(np.int16).tobytes())

            print(f"[INFO] Berhasil menyisipkan ke {output_path}")
            messagebox.showinfo("Berhasil", f"Tersimpan di: {output_path}")
        except Exception as e:
            print(f"[ERROR] {e}")
            messagebox.showerror("Error", f"Gagal menyisipkan: {e}")

    def extract_and_decrypt(self):
        try:
            with wave.open("embedded_output.wav", 'rb') as wave_read:
                frames = np.frombuffer(wave_read.readframes(wave_read.getnframes()), dtype=np.int16)

            header_bits = ""
            for i in range(16):
                delta = frames[i * 100]
                header_bits += '1' if delta > 200 else '0'

            bit_len = int(header_bits, 2)
            print(f"[DEBUG] Bitstream panjang dari header: {bit_len} bits")

            total_len = 16 + bit_len
            bits = ""
            for i in range(total_len):
                idx = i * 100
                if idx >= len(frames):
                    print(f"[WARN] Out of bounds at bit {i}")
                    break
                delta = frames[idx]
                bits += '1' if delta > 200 else '0'

            bits = bits[16:]

            byte_array = [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]
            encrypted = bytes(byte_array)
            print(f"[DEBUG] Encrypted length: {len(encrypted)} bytes")

            cipher = PKCS1_OAEP.new(self.rsa_key)
            decrypted = cipher.decrypt(encrypted)

            self.result_box.delete("1.0", tk.END)
            self.result_box.insert(tk.END, decrypted.decode())
            print(f"[INFO] Pesan berhasil didekripsi.")
        except Exception as e:
            print(f"[ERROR] Gagal mendekripsi: {e}")
            messagebox.showerror("Error", f"Gagal mendekripsi: {e}")

# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = RSAGUI(root)
    root.mainloop()
