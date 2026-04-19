"""Simple concurrency stress test for TCP Booking Server.

Run this while server.py is already running.
"""

from __future__ import annotations

import socket
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Final


HOST: Final[str] = "127.0.0.1"
PORT: Final[int] = 65432
BUFFER_SIZE: Final[int] = 1024


@dataclass
class ClientResult:
    client_id: int
    slot: str
    response: str
    error: str | None = None


def send_booking_request(client_id: int, slot: str, results: list[ClientResult], lock: threading.Lock) -> None:
    """Connect one client, send one BOOK command, and store result."""
    command = f"BOOK {slot}\n"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))

            # Read server welcome message.
            _ = sock.recv(BUFFER_SIZE)

            sock.sendall(command.encode("utf-8"))
            response = sock.recv(BUFFER_SIZE).decode("utf-8", errors="replace").strip()

            # Close cleanly.
            sock.sendall(b"QUIT\n")
            _ = sock.recv(BUFFER_SIZE)

        result = ClientResult(client_id=client_id, slot=slot, response=response)
    except OSError as exc:
        result = ClientResult(client_id=client_id, slot=slot, response="ERROR", error=str(exc))

    with lock:
        results.append(result)


def build_test_plan() -> list[str]:
    """Create overlapping booking targets to trigger contention."""
    return [
        "09:00-10:00",
        "09:00-10:00",
        "09:00-10:00",
        "09:00-10:00",
        "09:00-10:00",
        "09:00-10:00",
        "09:00-10:00",
        "09:00-10:00",
        "10:00-11:00",
        "11:00-12:00",
        "12:00-13:00",
    ]


def run_stress_test() -> None:
    """Run many client threads concurrently and print outcomes."""
    slots = build_test_plan()
    results: list[ClientResult] = []
    results_lock = threading.Lock()
    threads: list[threading.Thread] = []

    print("Starting stress test...")
    print(f"Target server: {HOST}:{PORT}")
    print(f"Total concurrent clients: {len(slots)}")

    start_time = time.perf_counter()

    for client_id, slot in enumerate(slots, start=1):
        thread = threading.Thread(
            target=send_booking_request,
            args=(client_id, slot, results, results_lock),
            daemon=True,
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    elapsed = time.perf_counter() - start_time

    # Stable output by client id.
    ordered_results = sorted(results, key=lambda item: item.client_id)

    print("\nPer-client results:")
    for item in ordered_results:
        if item.error is not None:
            print(f"Client {item.client_id:02d} | {item.slot} -> ERROR ({item.error})")
        else:
            print(f"Client {item.client_id:02d} | {item.slot} -> {item.response}")

    summary: dict[str, dict[str, int]] = defaultdict(lambda: {"OK": 0, "FAIL": 0, "OTHER": 0})
    for item in ordered_results:
        if item.response == "OK":
            summary[item.slot]["OK"] += 1
        elif item.response == "FAIL":
            summary[item.slot]["FAIL"] += 1
        else:
            summary[item.slot]["OTHER"] += 1

    print("\nSummary by slot:")
    for slot in sorted(summary.keys()):
        counts = summary[slot]
        print(
            f"{slot}: OK={counts['OK']} FAIL={counts['FAIL']} OTHER={counts['OTHER']}"
        )

    print(f"\nFinished in {elapsed:.3f}s")


if __name__ == "__main__":
    run_stress_test()
