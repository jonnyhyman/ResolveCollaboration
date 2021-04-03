from cryptography.fernet import Fernet, InvalidToken
import asyncio

import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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
UNAMES = ["Jonny", "Karlie"]
SPASS = passkey("test")
PKEYS = "TkUgP5YntnMghc9fs+2+SYJ55AZc6Yotl6qOrCmPLVQ="

# ------------- CONFIG
S_IP = '0.0.0.0' if not TEST else "127.0.0.1"
S_PORT = 4444

# ------------- COMMUNICATION

async def handle_authentication(reader, writer):
    auth_request = await reader.read(1024)
    fail_cause = "UNKNOWN ERROR"

    for UNAME in UNAMES:

        key = passkey(UNAME)

        try:
            message = Fernet(key).decrypt(auth_request)
            message = message.decode()

            addr = writer.get_extra_info('peername')
            print(f">>> Received {message} from {addr}")

            SPASS_CHECK, PKEYU = message.split(',')

            A = SPASS.decode()
            B = SPASS_CHECK

            if A == B:
                print("... Server password valid!")
            else:
                print('!!! Server password INVALID')
                print("...Need: ", A)
                print("... Got: ", B)
                continue

            ASSIGN_IP = "9.0.0.6"

            auth_reply = f"{PKEYS},{ASSIGN_IP}"
            auth_reply = Fernet(SPASS).encrypt(auth_reply.encode())
            writer.write(auth_reply)
            await writer.drain()

            print(f"... Authentication of {UNAME} complete!")
            break

        except InvalidToken as e:
            pass
    else:
        print(">>> Invalid request message (could be UNAME or SPASS)")
        writer.write("INVALID REQUEST".encode())

    writer.close()

loop = asyncio.get_event_loop()
coro = asyncio.start_server(handle_authentication, S_IP, S_PORT, loop=loop)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
print('... Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
