
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

        print("\033[1A\033[2K", end="", flush=True)
        writer.write((message + "\n").encode())
        await writer.drain()


async def main():

    reader, writer = await asyncio.open_connection(
        "127.0.0.1",
        5000
    )

    print("Connected to server")
    print("For annonimous chat, just press enter without typing a username.")

    while True:

        username = await asyncio.to_thread(input, "Username: ")

        writer.write((username + "\n").encode())
        await writer.drain()

        response = await reader.readline()
        if not response:
            raise ConnectionError(
                "Server disconnected during username selection"
            )
        response = response.decode().strip()

        if response == "Username accepted":
            break
        elif response == "Username already taken. Please choose another one.":
            print(response)
        elif response == (
            "Username cannot start or end with punctuation "
            "or whitespace. Please choose another one."
        ):
            print(response)
        else:
            raise RuntimeError(
                f"Unexpected response during username selection: {response}"
            )

    await asyncio.gather(
        receive_messages(reader),
        send_messages(writer)
    )


if __name__ == "__main__":
    asyncio.run(main())
