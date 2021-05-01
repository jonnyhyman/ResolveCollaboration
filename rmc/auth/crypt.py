import cryptography.hazmat.backends
default_backend = cryptography.hazmat.backends.default_backend

import cryptography.hazmat.primitives.kdf.pbkdf2
PBKDF2HMAC = cryptography.hazmat.primitives.kdf.pbkdf2.PBKDF2HMAC

import cryptography.fernet
Fernet = cryptography.fernet.Fernet
InvalidToken = cryptography.fernet.InvalidToken

import cryptography.hazmat.primitives
hashes = cryptography.hazmat.primitives.hashes

import base64

# helper functions
def passkey(password):
    password = password.encode()  # Convert to type bytes
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=password,
        iterations=100000,
        backend=default_backend()
    )
    # if anything, this is what gets saved in a database
    return base64.urlsafe_b64encode(kdf.derive(password))
