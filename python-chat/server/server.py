import asyncio

class ChatServer:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {}

    async def handle_client(self, reader, writer):

        address = writer.get_extra_info("peername")

        print(f"Client connected: {address}")

        try:
            while True:
                #this allows the server to handle other clients while this client is waiting for data
                #worst case scenario 1 client has shitty internet
                data = await reader.readline()

                if not data:
                    break

                message = data.decode().strip()

                print(f"Received: {message}")

        except ConnectionError:
            print(f"Connection Error! code:server.py")
            pass

        finally:
            writer.close()
            await writer.wait_closed()

            print(f"Client disconnected: {address}")

    async def start(self):

        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )

        print(f"Server running on {self.host}:{self.port}")

        async with server:
            await server.serve_forever()