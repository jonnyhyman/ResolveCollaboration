from cryptography.fernet import Fernet, InvalidToken
import asyncio
import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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

TEST = True
# ------------- INPUTS
UNAME = "Jonny"
SPASS = passkey("test")
PKEYU = "AObz7ylltQPyDXI11h1WWhPaEN60WN4Z0diOXBhAg0Q="
MESSG = f"{SPASS.decode()},{PKEYU}"
S_IP = '127.0.0.1' if TEST else "73.162.86.31"

# ------------- CONFIG
S_PORT = 4444

# ------------- COMMUNICATION

# Authentication request
encrypted = Fernet(passkey(UNAME)).encrypt(MESSG.encode())

async def tcp_authenticate_request(loop):
    print(">>> Connecting to", S_IP, S_PORT)
    reader, writer = await asyncio.open_connection(S_IP, S_PORT,
                                                   loop=loop)

    print('>>> Sent encrypted authentication request')
    writer.write(encrypted)

    auth_reply = await reader.read(1024)

    try:
        auth_reply = Fernet(SPASS).decrypt(auth_reply)
        auth_reply = auth_reply.decode()
        print(f">>> Received Authentication Reply: {auth_reply}")

    except InvalidToken as e:
        print(f"... Received Authentication Error: {auth_reply.decode()}")
        pass

    writer.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(tcp_authenticate_request(loop))
loop.close()
