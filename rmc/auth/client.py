from auth.crypt import InvalidToken, Fernet
import asyncio

async def tcp_authenticate_request(QUEUE, S_IP, S_PORT, SPASS, encrypted):
    """ TCP Client to connect to RMC Server """

    QUEUE.put(f"Connecting to server {S_IP}:{S_PORT}")
    try:
        reader, writer = await asyncio.open_connection(S_IP, S_PORT)
    except ConnectionRefusedError:
        QUEUE.put(f"Connection to server {S_IP}:{S_PORT} refused")
        return
    except TimeoutError:
        QUEUE.put(f"Connection to server {S_IP}:{S_PORT} timed out")
        return

    writer.write(encrypted)
    QUEUE.put('Sent encrypted authentication request')

    auth_reply = await reader.read(1024)

    try:
        auth_reply = Fernet(str(SPASS,'utf-8')).decrypt(auth_reply)
        auth_reply = auth_reply.decode()
        QUEUE.put(f"Server Authentication Reply: {auth_reply}")

        auth_reply = auth_reply.split(',')
        QUEUE.put(auth_reply)

    except InvalidToken as e:
        QUEUE.put(f"Server Authentication Error: {auth_reply.decode()}")

    writer.close()

def tcp_client(QUEUE, S_IP, S_PORT, SPASS, encrypted):
    """ QUEUE: multiprocessing.Queue for output and updates

        when QUEUE.put type is list, the request is complete!
    """

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(tcp_authenticate_request(QUEUE, S_IP, S_PORT, SPASS, encrypted))
    loop.close()
