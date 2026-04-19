"""TCP server that handles concurrent booking requests."""

from __future__ import annotations

import socket
import threading
from typing import Final

from booking_manager import BookingManager


HOST: Final[str] = "127.0.0.1"
PORT: Final[int] = 65432
BUFFER_SIZE: Final[int] = 1024


booking_manager = BookingManager()
BOOK_USAGE: Final[str] = "BOOK HH:MM-HH:MM"


def handle_client(conn: socket.socket, addr: tuple[str, int]) -> None:
    """Handle commands from one client connection."""
    client_label = f"{addr[0]}:{addr[1]}"
    print(f"[CONNECT] Client connected: {client_label}")

    with conn:
        conn.sendall(
            b"Welcome. Commands: BOOK HH:MM-HH:MM (example: BOOK 09:00-10:00), LIST (show all bookings), QUIT (exit)\n"
        )

        while True:
            try:
                data = conn.recv(BUFFER_SIZE)
            except ConnectionResetError:
                print(f"[DISCONNECT] Connection reset by: {client_label}")
                break

            if not data:
                print(f"[DISCONNECT] Client disconnected: {client_label}")
                break

            message = data.decode("utf-8", errors="replace").strip()
            if not message:
                continue

            print(f"[REQUEST] {client_label} -> {message}")
            response = process_command(message, client_label)

            conn.sendall((response + "\n").encode("utf-8"))
            if message.upper() == "QUIT":
                print(f"[DISCONNECT] Session closed for: {client_label}")
                break


def process_command(command: str, client_label: str) -> str:
    """Parse and execute one command."""
    normalized = command.strip()
    upper = normalized.upper()

    if upper == "QUIT":
        return "BYE"

    if upper == "LIST":
        slots = booking_manager.list_slots()
        if not slots:
            return "EMPTY"
        return "BOOKED " + ", ".join(slots)

    if upper == "BOOK" or upper.startswith("BOOK "):
        parts = normalized.split(maxsplit=1)
        if len(parts) != 2 or not parts[1].strip():
            return f"ERROR: Invalid command. Use: {BOOK_USAGE}"

        slot = parts[1].strip()

        try:
            success = booking_manager.book_slot(slot)
        except ValueError as error:
            print(f"[FAIL] Invalid slot from {client_label}: {slot}")
            return f"ERROR: {error}"

        if success:
            print(f"[BOOKED] {client_label} booked slot: {slot}")
            return "OK"

        print(f"[FAIL] Slot already taken ({slot}) for {client_label}")
        return "FAIL"

    return f"ERROR: Unknown command. Use: {BOOK_USAGE} | LIST | QUIT"


def start_server() -> None:
    """Start the TCP booking server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()

        print(f"[START] TCP Booking Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True,
            )
            client_thread.start()


if __name__ == "__main__":
    start_server()
