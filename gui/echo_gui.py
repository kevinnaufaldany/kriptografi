import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import wave
import matplotlib.pyplot as plt
import numpy as np

from core.echo_hiding import EchoHiding
from core.rsa_crypto import generate_keys, rsa_encrypt, rsa_decrypt, cipher_to_string, string_to_cipher
from utils.audio_utils import load_audio, save_audio


class EchoHidingGUI(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Echo Hiding + RSA Steganography")
        self.configure(bg="#f9f9f9")
        self.geometry("720x560")
        self.center_window()
        self.minsize(650, 500)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.echo = EchoHiding()
        self.e, self.d, self.n = generate_keys()

        self.audio_path = tk.StringVar()
        self.stego_path = tk.StringVar()

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()

        self.build_ui()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def configure_styles(self):
        self.style.configure("TFrame", background="#f9f9f9")
        self.style.configure("TLabelFrame", background="#f9f9f9", foreground="#222222", font=("Segoe UI", 11, "bold"))
        self.style.configure("TLabel", background="#f9f9f9", foreground="#222222", font=("Segoe UI", 10))
        self.style.configure("TButton",
                             background="#0066cc",
                             foreground="white",
                             font=("Segoe UI", 10, "bold"),
                             padding=6)
        self.style.map("TButton", background=[("active", "#004c99")])
        self.style.configure("TEntry", font=("Segoe UI", 10), padding=5)

    def build_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=15)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # === EMBED FRAME ===
        embed_frame = ttk.LabelFrame(main_frame, text="🔐 Embed Message")
        embed_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        embed_frame.columnconfigure(1, weight=1)

        ttk.Label(embed_frame, text="📝 Plaintext").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        self.msg_entry = ttk.Entry(embed_frame)
        self.msg_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=6)

        ttk.Label(embed_frame, text="🎧 Audio (WAV)").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        audio_frame = ttk.Frame(embed_frame)
        audio_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=6)
        audio_frame.columnconfigure(1, weight=1)

        ttk.Button(audio_frame, text="Browse...", command=self.select_audio).grid(row=0, column=0, sticky="w")
        self.audio_drop = tk.Label(audio_frame, text="⬇️ Drop WAV Here", relief="ridge", bg="#eaf4ff", fg="#004080",
                                font=("Segoe UI", 10, "bold"), height=2)
        self.audio_drop.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.audio_drop.drop_target_register(DND_FILES)
        self.audio_drop.dnd_bind('<<Drop>>', self.drop_audio)

        self.audio_info = tk.StringVar(value="🔍 No audio selected")
        ttk.Label(embed_frame, textvariable=self.audio_info, foreground="#666666", font=("Segoe UI", 9, "italic"))\
            .grid(row=2, column=1, sticky="w", padx=10, pady=(0, 5))

        ttk.Label(embed_frame, text="💾 Output Filename").grid(row=3, column=0, sticky="w", padx=10, pady=6)
        self.filename_entry = ttk.Entry(embed_frame)
        self.filename_entry.insert(0, "stego")
        self.filename_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=6)

        ttk.Button(embed_frame, text="🔒 Embed", command=self.embed).grid(row=4, column=1, sticky="e", pady=8, padx=10)

        # === EXTRACT FRAME ===
        extract_frame = ttk.LabelFrame(main_frame, text="🔓 Extract Message")
        extract_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        extract_frame.columnconfigure(1, weight=1)

        ttk.Label(extract_frame, text="🔊 Stego Audio").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        stego_frame = ttk.Frame(extract_frame)
        stego_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=6)
        stego_frame.columnconfigure(1, weight=1)

        ttk.Button(stego_frame, text="Browse...", command=self.select_stego).grid(row=0, column=0, sticky="w")
        self.stego_drop = tk.Label(stego_frame, text="⬇️ Drop WAV Here", relief="ridge", bg="#eaf4ff", fg="#004080",
                                font=("Segoe UI", 10, "bold"), height=2)
        self.stego_drop.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.stego_drop.drop_target_register(DND_FILES)
        self.stego_drop.dnd_bind('<<Drop>>', self.drop_stego)

        self.stego_info = tk.StringVar(value="🔍 No stego file selected")
        ttk.Label(extract_frame, textvariable=self.stego_info, foreground="#666666", font=("Segoe UI", 9, "italic"))\
            .grid(row=1, column=1, sticky="w", padx=10, pady=(0, 5))

        btn_frame = ttk.Frame(extract_frame)
        btn_frame.grid(row=2, column=1, sticky="e", padx=10, pady=(5, 10))
        ttk.Button(btn_frame, text="🔍 Extract", command=self.extract).grid(row=0, column=0, padx=5)
        ttk.Button(embed_frame, text="📈 Preview Waveform", command=self.plot_waveform).grid(row=5, column=1, sticky="e", padx=10, pady=(0, 8))


        self.result = tk.StringVar(value="Decrypted: -")
        ttk.Label(extract_frame, textvariable=self.result, font=("Segoe UI", 10, "italic"), foreground="#444444")\
            .grid(row=3, column=1, sticky="w", padx=10, pady=(0, 12))

    def update_audio_info(self, path, target_var):
        try:
            with wave.open(path, 'r') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
                file_name = os.path.basename(path)
                target_var.set(f"Duration: {duration:.2f} sec | File: {file_name}")
        except Exception as e:
            target_var.set("Failed to read audio info.")
            print("Error reading audio:", e)

    def drop_audio(self, event):
        path = event.data.strip("{}")
        if path.lower().endswith(".wav"):
            self.audio_path.set(path)
            self.update_audio_info(path, self.audio_info)
        else:
            messagebox.showerror("Format Error", "Only WAV files are allowed.")

    def drop_stego(self, event):
        path = event.data.strip("{}")
        if path.lower().endswith(".wav"):
            self.stego_path.set(path)
            self.update_audio_info(path, self.stego_info)
        else:
            messagebox.showerror("Format Error", "Only WAV files are allowed.")

    def select_audio(self):
        path = filedialog.askopenfilename(filetypes=[("WAV Files", "*.wav")])
        if path:
            self.audio_path.set(path)
            self.update_audio_info(path, self.audio_info)

    def select_stego(self):
        path = filedialog.askopenfilename(filetypes=[("WAV Files", "*.wav")])
        if path:
            self.stego_path.set(path)
            self.update_audio_info(path, self.stego_info)

    def embed(self):
        message = self.msg_entry.get()
        if not message:
            messagebox.showwarning("Warning", "Message cannot be empty!")
            return

        if not self.audio_path.get():
            messagebox.showwarning("Warning", "No audio selected!")
            return

        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showwarning("Warning", "Output filename cannot be empty!")
            return

        try:
            cipher = rsa_encrypt(message, self.e, self.n)
            cipher_str = cipher_to_string(cipher)
            audio_data, sr = load_audio(self.audio_path.get())
            stego = self.echo.embed_message(audio_data, cipher_str)
            os.makedirs("audio_out", exist_ok=True)
            output_path = f"audio_out/{filename}.wav"
            save_audio(output_path, stego, sr)
            messagebox.showinfo("Success", f"Message embedded successfully.\nSaved to '{output_path}'")
        except Exception as e:
            messagebox.showerror("Embed Error", str(e))

    def extract(self):
        if not self.stego_path.get():
            messagebox.showwarning("Warning", "No stego audio selected!")
            return

        try:
            audio_data, sr = load_audio(self.stego_path.get())
            cipher_str = self.echo.extract_message(audio_data)
            cipher = string_to_cipher(cipher_str)
            decrypted = rsa_decrypt(cipher, self.d, self.n)
            self.result.set(f"Decrypted: {decrypted}")
        except Exception as e:
            messagebox.showerror("Extract Error", str(e))

    def plot_waveform(self):
        if not self.audio_path.get():
            messagebox.showerror("Error", "Pilih audio asli terlebih dahulu!")
            return

        try:
            with wave.open(self.audio_path.get(), 'rb') as wf:
                n_frames = wf.getnframes()
                original_data = wf.readframes(n_frames)
                original_array = np.frombuffer(original_data, dtype=np.int16)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca audio asli:\n{e}")
            return

        # Default: stego dari audio_out, kecuali jika sudah pilih sendiri
        stego_file = self.stego_path.get()
        if not stego_file:
            filename = self.filename_entry.get().strip()
            stego_file = f"audio_out/{filename}.wav"

        stego_array = None
        try:
            if os.path.exists(stego_file):
                with wave.open(stego_file, 'rb') as wf2:
                    stego_data = wf2.readframes(wf2.getnframes())
                    stego_array = np.frombuffer(stego_data, dtype=np.int16)
            else:
                messagebox.showwarning("Stego Tidak Ditemukan", "File stego tidak ditemukan. Menampilkan hanya original.")
        except Exception as e:
            messagebox.showwarning("Gagal Membaca Stego", f"Gagal membaca file stego:\n{e}")

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
