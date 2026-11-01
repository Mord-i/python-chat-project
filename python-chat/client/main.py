
import asyncio


async def receive_messages(reader):

    while True:

        data = await reader.readline()

        if not data:
            print("Disconnected from server")
            break

        print(data.decode().strip())


async def send_messages(writer):

    while True:

        message = await asyncio.to_thread(input, "")

        if not message:
            continue

        writer.write((message + "\n").encode())
        await writer.drain()


async def main():

    reader, writer = await asyncio.open_connection(
        "127.0.0.1",
        5000
    )

    print("Connected to server")
    print("For annonimous chat, just press enter without typing a username.")
    username = input("Username: ")

    writer.write((username + "\n").encode())
    await writer.drain()

    await asyncio.gather(
        receive_messages(reader),
        send_messages(writer)
    )


if __name__ == "__main__":
    asyncio.run(main())
