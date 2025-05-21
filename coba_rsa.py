# === RSA Manual - Simple Demo ===

def power(base, expo, m):
    res = 1
    base %= m
    while expo > 0:
        if expo & 1:
            res = (res * base) % m
        base = (base * base) % m
        expo //= 2
    return res

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def modInverse(e, phi):
    for d in range(2, phi):
        if (e * d) % phi == 1:
            return d
    return -1

def generate_keys():
    p = 61
    q = 53
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 2
    while e < phi:
        if gcd(e, phi) == 1:
            break
        e += 1
    d = modInverse(e, phi)
    return (e, d, n)

# ==== Main Logic ====
plaintext = "hi nama aku Freddy"
print("[PLAINTEXT]:", plaintext)

# Konversi plaintext ke angka ASCII
ascii_values = [ord(c) for c in plaintext]
print("[ASCII VALUES]:", ascii_values)

# Generate key
e, d, n = generate_keys()
print(f"[RSA KEYS] Public Key (e, n): ({e}, {n}), Private Key (d, n): ({d}, {n})")

# Enkripsi
encrypted = [power(m, e, n) for m in ascii_values]
print("[ENCRYPTED]:", encrypted)

# Dekripsi
decrypted = [chr(power(c, d, n)) for c in encrypted]
decrypted_text = ''.join(decrypted)
print("[DECRYPTED TEXT]:", decrypted_text)
