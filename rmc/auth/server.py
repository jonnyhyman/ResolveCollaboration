from auth.crypt import passkey, Fernet, InvalidToken
import asyncio

async def handle_authentication(reader, writer, QUEUE,
                                                userlist, server_pass, wg_port):
    auth_request = await reader.read(1024)
    fail_cause = "UNKNOWN ERROR"

    for user in userlist: # skip server
        # loop through usernames, see if one properly decrpyts message
        # hash key to decrypt message with:
        key = str(passkey(user['name']), 'utf-8')

        try:

            addr = writer.get_extra_info('peername')
            # QUEUE.put(f">>> Received {message} from {addr}")

            # decrypt message
            message = Fernet(key).decrypt(auth_request)
            message = message.decode()

            PASS_CHECK, PKEYU = message.split(',')

            if server_pass == PASS_CHECK:
                QUEUE.put("Server password valid!")
                print("... Server password valid!")
            else:
                QUEUE.put('Server password invalid')
                print("... Server password invalid!")
                continue

            PKEYS = userlist[0]['Pk']
            SERVER_IP = userlist[0]['ip']
            ASSIGN_IP = user['ip']
            WG_PORT = wg_port

            auth_reply = f"{PKEYS},{SERVER_IP},{ASSIGN_IP},{WG_PORT}"
            auth_reply = Fernet(server_pass).encrypt(auth_reply.encode())
            writer.write(auth_reply)
            await writer.drain()

            QUEUE.put(f"... Authentication of {user['name']} complete!")
            QUEUE.put([user['name'], PKEYU])
            print("... Authentication complete, on to Wireguard reconfig")
            break

        except InvalidToken as e:
            # invalid username (not in userlist)
            print(f'... {user} did not decrypt message from {addr}')
            pass
    else:
        QUEUE.put("Invalid request message (Invalid username or server password)")
        writer.write("INVALID REQUEST".encode())

    writer.close()

def tcp_server(QUEUE, S_IP, S_PORT, userlist, server_pass, wg_port):
    """ QUEUE: multiprocessing.Queue for output and updates
        when latest QUEUE item type is list, the request is complete!
    """

    loop = asyncio.new_event_loop()
    authentication = loop.create_future()
    asyncio.set_event_loop(loop)

    handle_authentication_ = lambda r,w: handle_authentication(r,w,
                                                            QUEUE,
                                                            userlist,
                                                            server_pass,
                                                            wg_port
                                                            )

    coro = asyncio.start_server(handle_authentication_, S_IP, S_PORT, loop=loop)

    try:
        async_server = loop.run_until_complete(coro)
    except OSError as e:
        # The port is already in use
        QUEUE.put(e)
        return

    # Serve requests until Ctrl+C is pressed
    QUEUE.put('... Authentication serving on {}'.format(async_server.sockets[0].getsockname()))

    try:
        loop.run_until_complete(authentication)
    except KeyboardInterrupt:
        pass

    # Close the server
    async_server.close()
    loop.run_until_complete(async_server.wait_closed())
    loop.close()
