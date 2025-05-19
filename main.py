import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import io
import encrypt_aes_cfb
import echo_hiding

class KriptoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AES-CFB + Echo Hiding Steganography")

        tk.Button(root, text="Pilih Gambar", command=self.load_image).pack(pady=10)
        tk.Button(root, text="Pilih Audio", command=self.load_audio).pack(pady=10)
        tk.Button(root, text="Proses Enkripsi + Sisip", command=self.process).pack(pady=10)

        self.image_path = None
        self.audio_path = None

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png"), ("All files", "*.*")])
        if path:
            self.image_path = path
            messagebox.showinfo("Info", f"Gambar dipilih: {path}")

    def load_audio(self):
        path = filedialog.askopenfilename(filetypes=[("WAV", "*.wav"), ("All files", "*.*")])
        if path:
            self.audio_path = path
            messagebox.showinfo("Info", f"Audio dipilih: {path}")

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
        messagebox.showinfo("Sukses", f"Stego audio disimpan di {output_audio}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KriptoGUI(root)
    root.mainloop()
