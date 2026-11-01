import asyncio
import json

class ChatConnection:

    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def connect(self):

        self.reader, self.writer = await asyncio.open_connection(
            self.host,
            self.port
        )

    async def send_message(self, message):

        data = json.dumps(message) + "\n"

        self.writer.write(data.encode())

        await self.writer.drain()

    async def receive_messages(self):

        while True:

            data = await self.reader.readline()

            if not data:
                break

            message = json.loads(data.decode())

            print(message)