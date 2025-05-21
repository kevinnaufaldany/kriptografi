import time
import random
from core.rsa_crypto import generate_keys, rsa_encrypt, rsa_decrypt

def evaluate_rsa_time():
    e, d, n = generate_keys()
    for length in [5, 50, 100]:
        plaintext = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=length))
        print(f"\n[INFO] Testing with plaintext length: {length} characters")

        start_enc = time.perf_counter()
        ciphertext = rsa_encrypt(plaintext, e, n)
        end_enc = time.perf_counter()

        start_dec = time.perf_counter()
        decrypted = rsa_decrypt(ciphertext, d, n)
        end_dec = time.perf_counter()

        print(f"  Encryption time: {end_enc - start_enc:.6f} s")
        print(f"  Decryption time: {end_dec - start_dec:.6f} s")

def evaluate_avalanche_effect():
    e, d, n = generate_keys()
    base_plain = "HELLO_WORLD"
    mod_plain = "HELLO_WORLE"  # hanya 1 karakter beda

    cipher1 = rsa_encrypt(base_plain, e, n)
    cipher2 = rsa_encrypt(mod_plain, e, n)

    if len(cipher1) != len(cipher2):
        min_len = min(len(cipher1), len(cipher2))
        cipher1 = cipher1[:min_len]
        cipher2 = cipher2[:min_len]

    bit_diff = 0
    total_bits = 0

    for c1, c2 in zip(cipher1, cipher2):
        xor = c1 ^ c2
        bit_diff += bin(xor).count('1')
        total_bits += max(c1.bit_length(), c2.bit_length())

    percentage = (bit_diff / total_bits) * 100
    print(f"\n[INFO] Avalanche Effect:")
    print(f"  Total bits compared: {total_bits}")
    print(f"  Bits changed: {bit_diff}")
    print(f"  Change percentage: {percentage:.2f}%")

def calculate_ber(original_bits, extracted_bits):
    min_len = min(len(original_bits), len(extracted_bits))
    errors = sum(o != e for o, e in zip(original_bits[:min_len], extracted_bits[:min_len]))
    ber = errors / min_len
    print(f"[INFO] Bit Error Rate (BER): {ber:.6f} ({errors} bit errors of {min_len})")
    return ber

if __name__ == "__main__":
    evaluate_rsa_time()
    evaluate_avalanche_effect()

    # Dummy test BER
    original_bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    extracted_bits = [1, 0, 0, 1, 0, 1, 1, 0, 1, 1]
    calculate_ber(original_bits, extracted_bits)

