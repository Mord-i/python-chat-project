import asyncio
import random
import string

class ChatServer:

    def __init__(self):
        self.clients = {}
        self.rooms = {
            "general": set()
        }

    async def handle_client(self, reader, writer):

        address = writer.get_extra_info("peername")
        username = None
        current_room = None

        print(f"Connection from: {address}")

        try:
            #Receive the username from the client
            data = await reader.readline()
            #username = data.decode().strip()

            if not username:
                while True:
                    username = f"User{random.randint(10000, 99999)}"

                    existing_users = [
                        client["username"]
                        for client in self.clients.values()
                    ]

                    if username not in existing_users:
                        break
            #TODO username uniqeness

            else:
                while True:
                    username = data.decode().strip()

                    existing_users = [
                        client["username"]
                        for client in self.clients.values()
                    ]

                    if username in existing_users:
                        break

            self.clients[writer] = {
                "username": username,
                "room": None
            }

            writer.write(f"Welcome to the chat server {username}!\n".encode())
            await writer.drain()

            print(f"User '{username}' connected from {address}")

            while True:

                data = await reader.readline()

                if not data:
                    break

                message = data.decode().strip()

                if not message:
                    continue

                #commands
                if message.startswith("/"):
                    current_room = await self.handle_command(
                        message, writer, username, current_room
                    )

                else:
                    if current_room is None:
                        writer.write(
                            b"Join a room first using /join <room_name> before sending messages.\n"
                        )
                        await writer.drain()
                        continue

                    await self.broadcast(
                        current_room,
                        f"[{current_room}] {username}: {message}",
                        exclude=None
                    )

        except ConnectionError:
            pass

        finally:
            if current_room:
                await self.leave_room(writer, username, current_room)

            self.clients.pop(writer, None)

            writer.close()
            await writer.wait_closed()

            print(f"{username} disconnected from {address}")

    async def handle_command(
            self, command, writer, username, current_room
    ):

        parts = command.split()
        action = parts[0].lower()

        if action == "/join":

            if len(parts) < 2:
                writer.write(b"Usage: /join <room_name>\n")
                await writer.drain()
                return current_room

            new_room = parts[1].lower()

            if current_room:
                await self.leave_room(
                    writer, username, current_room
                )

            if new_room not in self.rooms:
                self.rooms[new_room] = set()

            self.rooms[new_room].add(writer)
            self.clients[writer]["room"] = new_room

            await self.send(writer, f"Joined room: {new_room}\n")

            await self.broadcast(
                new_room,
                f"{username} has joined the room.\n",
                exclude=writer
            )

            return new_room

        elif action == "/leave":

            if current_room:
                await self.leave_room(
                    writer, username, current_room
                )

            await self.send(writer, "You left the room")

            return None

        elif action == "/rooms":

            room_list = ", ".join(
                f"{name} ({len(members)} users)"
                for name, members in self.rooms.items()
            )

            await self.send(writer, f"Rooms: {room_list}")

        elif action == "/users":

            if current_room is None:
                await self.send(writer, "You are not in a room")
            else:
                users = [
                    self.clients[client]["username"]
                    for client in self.rooms[current_room]
                    if client in self.clients
                ]

                await self.send(
                    writer,
                    f"Users in {current_room}: {', '.join(users)}"
                )

        elif action == "/help":

            await self.send(
                writer,
                "/join roomname | /leave | /rooms | /users | /help"
            )

        else:
            await self.send(writer, "Unknown command")

        return current_room

    async def leave_room(self, writer, username, room):

        if room not in self.rooms:
            return

        self.rooms[room].discard(writer)

        if writer in self.clients:
            self.clients[writer]["room"] = None

        await self.broadcast(
            room,
            f"{username} left the room",
            exclude=writer
        )

        # Delete empty rooms except general
        if not self.rooms[room] and room != "general":
            del self.rooms[room]

    async def broadcast(self, room, message, exclude=None):

        if room not in self.rooms:
            return

        for client in list(self.rooms[room]):

            if client == exclude:
                continue

            await self.send(client, message)

    async def send(self, writer, message):

        writer.write((message + "\n").encode())
        await writer.drain()

    async def start(self):

        port_number = 5000
        server = await asyncio.start_server(
            self.handle_client,
            "0.0.0.0",
            port_number
        )

        print(f"Chat server running on port {port_number}")

        async with server:
            await server.serve_forever()


async def main():

    chat_server = ChatServer()
    await chat_server.start()


if __name__ == "__main__":
    asyncio.run(main())
