import socket
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox


HOST = "127.0.0.1"
PORT = 5000


class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Application")
        self.root.geometry("850x600")
        self.root.minsize(650, 450)

        self.sock = None
        self.reader = None
        self.connected = False
        self.closing = False
        self.events = queue.Queue()
        self.username_attempts = queue.Queue()
        self.login_waiting = False

        self.current_room = None
        self.username = ""

        self._configure_style()
        self._build_login()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._process_events)

    def _configure_style(self):
        self.root.configure(bg="#17212b")
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TFrame", background="#17212b"
        )
        style.configure(
            "TLabel", background="#17212b", foreground="#e8eef5",
            font=("Segoe UI", 10)
        )
        style.configure(
            "Title.TLabel", font=("Segoe UI", 21, "bold"),
            foreground="#ffffff"
        )
        style.configure(
            "Muted.TLabel", foreground="#a9b7c6"
        )
        style.configure(
            "TButton", font=("Segoe UI", 10), padding=(10, 7)
        )
        style.configure(
            "Accent.TButton", background="#2388d1",
            foreground="white", font=("Segoe UI", 10, "bold")
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#1673b8"), ("disabled", "#526575")]
        )
        style.configure(
            "TEntry", padding=8, fieldbackground="#243443",
            foreground="#ffffff"
        )

    def _build_login(self):
        self.login_frame = ttk.Frame(self.root, padding=35)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(
            self.login_frame, text="CHAT ROOM", style="Title.TLabel"
        ).pack(pady=(0, 8))
        ttk.Label(
            self.login_frame,
            text="Connect to the chat server",
            style="Muted.TLabel"
        ).pack(pady=(0, 25))

        ttk.Label(self.login_frame, text="Username").pack(anchor="w")
        self.username_entry = ttk.Entry(
            self.login_frame, width=34, font=("Segoe UI", 11)
        )
        self.username_entry.pack(pady=(6, 12))
        self.username_entry.bind("<Return>", lambda _event: self.connect())

        self.connect_button = ttk.Button(
            self.login_frame, text="Connect",
            style="Accent.TButton", command=self.connect
        )
        self.connect_button.pack(fill="x")

        self.login_status = ttk.Label(
            self.login_frame, text="Leave the name empty to connect anonymously.",
            style="Muted.TLabel", wraplength=300
        )
        self.login_status.pack(pady=(15, 0))

    def connect(self):
        if self.connected:
            return

        username = self.username_entry.get()
        self.connect_button.configure(state="disabled")

        if self.login_waiting:
            self.login_waiting = False
            self.username_attempts.put(username)
            self.login_status.configure(text="Checking username...")
            return

        self.login_status.configure(text="Connecting to the server...")
        threading.Thread(
            target=self._connection_worker,
            args=(username,),
            daemon=True
        ).start()

    def _connection_worker(self, first_username):
        try:
            self.sock = socket.create_connection((HOST, PORT), timeout=8)
            self.sock.settimeout(None)
            self.reader = self.sock.makefile(
                "r", encoding="utf-8", newline="\n"
            )

            username = first_username
            while not self.closing:
                self.sock.sendall((username + "\n").encode("utf-8"))
                response = self.reader.readline()

                if not response:
                    raise ConnectionError(
                        "The server closed the connection."
                    )

                response = response.rstrip("\r\n")
                if response == "Username accepted":
                    self.username = username
                    self.events.put(("connected", username))
                    break

                if response in (
                    "Username already taken. Please choose another one.",
                    "Username cannot start or end with punctuation "
                    "or whitespace. Please choose another one."
                ):
                    self.events.put(("login_error", response))
                    username = self.username_attempts.get()
                    continue

                raise RuntimeError(response)

            if self.closing:
                return

            while not self.closing:
                line = self.reader.readline()
                if not line:
                    raise ConnectionError("The server disconnected.")
                self.events.put(("message", line.rstrip("\r\n")))

        except Exception as exc:
            self.events.put(("connection_error", str(exc)))

    def _build_chat(self):
        self.login_frame.destroy()

        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(
            header, text="CHAT ROOM", style="Title.TLabel"
        ).pack(side="left")

        self.identity_label = ttk.Label(
            header, text=f"Logged in as: {self.username or 'anonymous'}",
            style="Muted.TLabel"
        )
        self.identity_label.pack(side="right", padx=(8, 0))

        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)

        chat_panel = ttk.Frame(body)
        chat_panel.pack(side="left", fill="both", expand=True)

        self.chat_text = tk.Text(
            chat_panel, wrap="word", state="disabled",
            bg="#101a23", fg="#e8eef5",
            insertbackground="white", relief="flat",
            padx=14, pady=12, font=("Segoe UI", 10),
            selectbackground="#28618a"
        )
        scrollbar = ttk.Scrollbar(
            chat_panel, orient="vertical", command=self.chat_text.yview
        )
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        self.chat_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.chat_text.tag_configure(
            "system", foreground="#8fb9d8"
        )
        self.chat_text.tag_configure(
            "normal", foreground="#e8eef5"
        )

        side = ttk.Frame(body, padding=(12, 0, 0, 0))
        side.pack(side="right", fill="y")

        ttk.Label(side, text="Rooms and commands").pack(
            anchor="w", pady=(0, 8)
        )

        self.room_entry = ttk.Entry(side, width=19)
        self.room_entry.pack(fill="x", pady=(0, 6))
        self.room_entry.insert(0, "general")
        self.room_entry.bind(
            "<Return>", lambda _event: self.join_room()
        )

        ttk.Button(
            side, text="Join room",
            style="Accent.TButton", command=self.join_room
        ).pack(fill="x", pady=3)

        ttk.Button(
            side, text="Leave room",
            command=lambda: self.send_command("/leave")
        ).pack(fill="x", pady=3)

        ttk.Separator(side).pack(fill="x", pady=10)

        ttk.Button(
            side, text="List rooms",
            command=lambda: self.send_command("/rooms")
        ).pack(fill="x", pady=3)

        ttk.Button(
            side, text="Room users",
            command=lambda: self.send_command("/users")
        ).pack(fill="x", pady=3)

        ttk.Button(
            side, text="Help",
            command=lambda: self.send_command("/help")
        ).pack(fill="x", pady=3)

        self.room_status = ttk.Label(
            side, text="Current room: none",
            style="Muted.TLabel", wraplength=150
        )
        self.room_status.pack(anchor="w", pady=(15, 0))

        compose = ttk.Frame(outer)
        compose.pack(fill="x", pady=(12, 0))

        self.message_entry = ttk.Entry(
            compose, font=("Segoe UI", 11)
        )
        self.message_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        self.message_entry.bind(
            "<Return>", lambda _event: self.send_message()
        )

        ttk.Button(
            compose, text="Send",
            style="Accent.TButton", command=self.send_message
        ).pack(side="right")

        self.message_entry.focus_set()
        self._append_message(
            "You are connected. Join a room first with the /join command "
            "or by using the field on the right.",
            system=True
        )

    def join_room(self):
        room = self.room_entry.get().strip()
        if not room:
            self._append_message("Enter a room name.", system=True)
            return
        self.send_command(f"/join {room}")

    def send_command(self, command):
        self._send_raw(command)

    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return
        self._send_raw(message)
        self.message_entry.delete(0, "end")

    def _send_raw(self, message):
        if not self.connected or not self.sock:
            return
        try:
            self.sock.sendall((message + "\n").encode("utf-8"))
        except OSError as exc:
            self._append_message(
                f"Could not send the message: {exc}",
                system=True
            )

    def _append_message(self, message, system=False):
        self.chat_text.configure(state="normal")
        self.chat_text.insert(
            "end", message + "\n",
            "system" if system else "normal"
        )
        self.chat_text.see("end")
        self.chat_text.configure(state="disabled")

    def _process_events(self):
        try:
            while True:
                event, value = self.events.get_nowait()

                if event == "connected":
                    self.connected = True
                    self._build_chat()

                elif event == "login_error":
                    self.login_waiting = True
                    self.login_status.configure(text=value)
                    self.connect_button.configure(state="normal")
                    self.username_entry.focus_set()
                    self.username_entry.selection_range(0, "end")

                elif event == "message":
                    if value.startswith("Welcome to the chat server "):
                        self.username = value[
                            len("Welcome to the chat server "):-1
                        ]

                        self.identity_label.configure(
                            text=f"Logged in as: {self.username}"
                        )
                    self._append_message(value, system=(
                        value.startswith("Joined room:")
                        or value.startswith("You left the room")
                        or value.startswith("Rooms:")
                        or value.startswith("Users in ")
                        or value.startswith("Join a room first")
                        or value.startswith("Usage:")
                        or value.startswith("/join")
                        or value.startswith("Unknown command")
                        or value.startswith("Welcome to the chat server")
                    ))

                    if value.startswith("Joined room:"):
                        self.current_room = value.split(":", 1)[1].strip()
                        self.room_status.configure(
                            text=f"Current room: {self.current_room}"
                        )
                    elif value == "You left the room":
                        self.current_room = None
                        self.room_status.configure(
                            text="Current room: none"
                        )

                elif event == "connection_error":
                    if self.connected:
                        self._append_message(
                            f"Connection error: {value}", system=True
                        )
                        self.connected = False
                    else:
                        self.login_status.configure(
                            text=f"Could not connect: {value}"
                        )
                        self.connect_button.configure(state="normal")
                        if self.sock:
                            try:
                                self.sock.close()
                            except OSError:
                                pass
                        self.sock = None

        except queue.Empty:
            pass

        if not self.closing:
            self.root.after(100, self._process_events)

    def close(self):
        self.closing = True
        self.connected = False
        try:
            if self.sock:
                self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()
