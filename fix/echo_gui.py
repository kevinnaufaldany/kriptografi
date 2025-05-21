import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import wave

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
        main_frame.rowconfigure(0, weight=0)
        main_frame.rowconfigure(1, weight=1)

        # --- Embed Frame ---
        embed_frame = ttk.LabelFrame(main_frame, text="Embed Message")
        embed_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=10)
        embed_frame.columnconfigure(1, weight=1)

        ttk.Label(embed_frame, text="Plaintext").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        self.msg_entry = ttk.Entry(embed_frame)
        self.msg_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=6)

        ttk.Label(embed_frame, text="Audio (WAV)").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        audio_frame = ttk.Frame(embed_frame)
        audio_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=6)
        audio_frame.columnconfigure(1, weight=1)

        ttk.Button(audio_frame, text="Select Audio", command=self.select_audio).grid(row=0, column=0, sticky="w")
        self.audio_drop = tk.Label(audio_frame, text="Drop WAV Here", relief="ridge", bg="white",
                                   fg="#0066cc", font=("Segoe UI", 10, "bold"))
        self.audio_drop.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.audio_drop.drop_target_register(DND_FILES)
        self.audio_drop.dnd_bind('<<Drop>>', self.drop_audio)

        self.audio_info = tk.StringVar(value="No audio selected")
        ttk.Label(embed_frame, textvariable=self.audio_info, foreground="#555555").grid(row=2, column=1, sticky="w", padx=10)

        ttk.Label(embed_frame, text="Output Filename").grid(row=3, column=0, sticky="w", padx=10, pady=6)
        self.filename_entry = ttk.Entry(embed_frame)
        self.filename_entry.insert(0, "stego")  # default name
        self.filename_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=6)

        ttk.Button(embed_frame, text="Embed", command=self.embed).grid(row=4, column=1, sticky="e", pady=10, padx=10)

        # --- Extract Frame ---
        extract_frame = ttk.LabelFrame(main_frame, text="Extract Message")
        extract_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        extract_frame.columnconfigure(1, weight=1)

        ttk.Label(extract_frame, text="Stego Audio (WAV)").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        stego_frame = ttk.Frame(extract_frame)
        stego_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=6)
        stego_frame.columnconfigure(1, weight=1)

        ttk.Button(stego_frame, text="Select Stego", command=self.select_stego).grid(row=0, column=0, sticky="w")
        self.stego_drop = tk.Label(stego_frame, text="Drop WAV Here", relief="ridge", bg="white",
                                   fg="#0066cc", font=("Segoe UI", 10, "bold"))
        self.stego_drop.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.stego_drop.drop_target_register(DND_FILES)
        self.stego_drop.dnd_bind('<<Drop>>', self.drop_stego)

        self.stego_info = tk.StringVar(value="No stego file selected")
        ttk.Label(extract_frame, textvariable=self.stego_info, foreground="#555555").grid(row=1, column=1, sticky="w", padx=10)

        ttk.Button(extract_frame, text="Extract", command=self.extract).grid(row=2, column=1, sticky="e", pady=10, padx=10)

        self.result = tk.StringVar(value="Decrypted: -")
        ttk.Label(extract_frame, textvariable=self.result, font=("Segoe UI", 10, "italic"), foreground="#444444").grid(row=3, column=1, sticky="w", padx=10, pady=(0, 12))

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

