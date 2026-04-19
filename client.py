"""Simple TCP client for the booking server."""

from __future__ import annotations

import socket
from typing import Final


HOST: Final[str] = "127.0.0.1"
PORT: Final[int] = 65432
BUFFER_SIZE: Final[int] = 1024


def start_client() -> None:
    """Connect to server and send user commands."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        welcome = client_socket.recv(BUFFER_SIZE).decode("utf-8", errors="replace").strip()
        print(f"[SERVER] {welcome}")

        print("Type commands:")
        print("  BOOK HH:MM-HH:MM  -> reserve a slot (example: BOOK 09:00-10:00)")
        print("  LIST              -> show all current bookings")
        print("  QUIT              -> close the client")

        while True:
            command = input("> ").strip()
            if not command:
                continue

            client_socket.sendall((command + "\n").encode("utf-8"))
            response = client_socket.recv(BUFFER_SIZE).decode("utf-8", errors="replace").strip()
            print(f"[SERVER] {response}")

            if command.upper() == "QUIT":
                break


if __name__ == "__main__":
    try:
        start_client()
    except ConnectionRefusedError:
        print(f"Could not connect to server at {HOST}:{PORT}. Start server first.")
