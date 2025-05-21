def gcd(a, b):
    while b: a, b = b, a % b
    return a

def mod_inverse(e, phi):
    for d in range(2, phi):
        if (e * d) % phi == 1:
            return d
    return None

def generate_keys():
    p, q = 7919, 1009
    n = p * q
    phi = (p-1)*(q-1)
    e = next(x for x in range(2, phi) if gcd(x, phi) == 1)
    d = mod_inverse(e, phi)
    return e, d, n

def rsa_encrypt(message, e, n):
    return [pow(ord(c), e, n) for c in message]

def rsa_decrypt(ciphertext, d, n):
    return ''.join(chr(pow(c, d, n)) for c in ciphertext)

def cipher_to_string(cipher):
    return ','.join(map(str, cipher))

def string_to_cipher(s):
    return list(map(int, s.split(',')))
