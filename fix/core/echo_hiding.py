import numpy as np
import scipy.signal as signal

class EchoHiding:
    def __init__(self, d0=150, d1=200, alpha=0.5, frame_length=8192):
        self.d0 = d0
        self.d1 = d1
        self.alpha = alpha
        self.frame_length = frame_length

    def text_to_bits(self, text):
        return ''.join(format(ord(c), '08b') for c in text)

    def bits_to_text(self, bits):
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            chars.append(chr(int(byte, 2)))
        return ''.join(chars)

    def create_echo_kernel(self, delay):
        kernel = np.zeros(delay + 1)
        kernel[0] = 1
        kernel[delay] = self.alpha
        return kernel

    def embed_bits(self, signal_data, bit_sequence):
        kernel0 = self.create_echo_kernel(self.d0)
        kernel1 = self.create_echo_kernel(self.d1)
        echo0 = signal.lfilter(kernel0, 1, signal_data)
        echo1 = signal.lfilter(kernel1, 1, signal_data)

        n = len(bit_sequence) * self.frame_length
        mixer = np.zeros(n)
        for i, b in enumerate(bit_sequence):
            start = i * self.frame_length
            end = start + self.frame_length
            mixer[start:end] = int(b)

        stego = signal_data[:n] + (1 - mixer) * (echo0[:n] - signal_data[:n]) + mixer * (echo1[:n] - signal_data[:n])
        return np.concatenate([stego, signal_data[n:]])

    def extract_bits(self, stego_signal, total_bits):
        bits = ''
        for i in range(total_bits):
            start = i * self.frame_length
            end = start + self.frame_length
            frame = stego_signal[start:end]
            cepstrum = np.real(np.fft.ifft(np.log(np.abs(np.fft.fft(frame)) + 1e-10)))
            bits += '0' if cepstrum[self.d0] >= cepstrum[self.d1] else '1'
        return bits

    def embed_message(self, audio_signal, message):
        bit_sequence = self.text_to_bits(message)
        prefix = format(len(message), '016b')  # Panjang pesan dalam 16 bit
        return self.embed_bits(audio_signal, prefix + bit_sequence)

    def extract_message(self, stego_signal):
        length_bits = self.extract_bits(stego_signal, 16)
        message_length = int(length_bits, 2)
        message_bits = self.extract_bits(stego_signal, 16 + message_length * 8)[16:]
        return self.bits_to_text(message_bits)
