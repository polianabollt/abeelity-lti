# generate_keys.py
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import json
import base64

def to_base64url_uint(val):
    return base64.urlsafe_b64encode(val.to_bytes((val.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8')

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
private_pem = key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
)

public_key = key.public_key()
numbers = public_key.public_numbers()

jwk = {
    "kty": "RSA",
    "use": "sig",
    "kid": "chave-123",
    "alg": "RS256",
    "n": to_base64url_uint(numbers.n),
    "e": to_base64url_uint(numbers.e)
}

with open("private_key.pem", "wb") as f:
    f.write(private_pem)

with open("jwks.json", "w") as f:
    json.dump({ "keys": [jwk] }, f, indent=2)

print("✅ Chaves geradas com sucesso.")
