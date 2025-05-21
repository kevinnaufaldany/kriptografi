import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from core.echo_hiding import EchoHiding
from core.rsa_crypto import generate_keys, rsa_encrypt, rsa_decrypt, cipher_to_string, string_to_cipher
from utils.audio_utils import load_audio, save_audio

class EchoHidingGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Echo Hiding + RSA")
        self.geometry("600x300")
        self.echo = EchoHiding()
        self.e, self.d, self.n = generate_keys()
        self.build_ui()

    def build_ui(self):
        # Embed
        ttk.Label(self, text="Plaintext").grid(row=0, column=0, sticky="w")
        self.msg_entry = tk.Entry(self, width=50)
        self.msg_entry.grid(row=0, column=1)

        ttk.Button(self, text="Select Audio", command=self.select_audio).grid(row=1, column=0)
        self.audio_path = tk.StringVar()
        tk.Label(self, textvariable=self.audio_path).grid(row=1, column=1, sticky="w")

        ttk.Button(self, text="Embed", command=self.embed).grid(row=2, column=0)

        # Extract
        ttk.Button(self, text="Select Stego", command=self.select_stego).grid(row=3, column=0)
        self.stego_path = tk.StringVar()
        tk.Label(self, textvariable=self.stego_path).grid(row=3, column=1, sticky="w")

        ttk.Button(self, text="Extract", command=self.extract).grid(row=4, column=0)
        self.result = tk.StringVar()
        tk.Label(self, textvariable=self.result).grid(row=4, column=1, sticky="w")

    def select_audio(self):
        path = filedialog.askopenfilename(filetypes=[("WAV Files", "*.wav")])
        if path:
            self.audio_path.set(path)

    def select_stego(self):
        path = filedialog.askopenfilename(filetypes=[("WAV Files", "*.wav")])
        if path:
            self.stego_path.set(path)

    def embed(self):
        message = self.msg_entry.get()
        if not message:
            messagebox.showwarning("Error", "Message empty")
            return

        cipher = rsa_encrypt(message, self.e, self.n)
        cipher_str = cipher_to_string(cipher)

        audio_data, sr = load_audio(self.audio_path.get())
        stego = self.echo.embed_message(audio_data, cipher_str)
        save_audio("audio_out/stego.wav", stego, sr)
        messagebox.showinfo("Success", "Message embedded with RSA and saved.")

    def extract(self):
        audio_data, sr = load_audio(self.stego_path.get())
        cipher_str = self.echo.extract_message(audio_data)
        cipher = string_to_cipher(cipher_str)
        decrypted = rsa_decrypt(cipher, self.d, self.n)
        self.result.set(f"Decrypted: {decrypted}")
