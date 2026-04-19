# TCP Booking Server
This project demonstrates how multiple concurrent clients compete over shared resources and how synchronization ensures consistency.

## Project Purpose

`TCP Booking Server` is a small Python 3.11 interview-friendly project that demonstrates:

- TCP socket communication
- Handling multiple clients concurrently with threads
- Protecting shared in-memory state with locks
- Preventing double-booking of the same time slot

It uses only the Python standard library.

## Architecture

The project has four files:

- `server.py`
  - Starts a TCP server on `127.0.0.1:65432`
  - Accepts multiple clients concurrently
  - Parses commands and returns responses (`OK`, `FAIL`, etc.)
  - Logs connections, requests, booking success, and failures
- `booking_manager.py`
  - Contains `BookingManager`
  - Stores booked slots in memory (`set[str]`)
  - Uses `threading.Lock` for thread-safe access
- `client.py`
  - Simple interactive TCP client
  - Sends user commands to the server and prints responses
- `README.md`
  - Documentation and usage examples

## Features
- Multi-client TCP server
- Concurrent booking handling
- Synchronization to prevent double booking
- Stress testing with concurrent clients

## Concurrency Handling

- The server creates a new thread for each client connection (`threading.Thread`).
- All clients share one `BookingManager` instance.
- `BookingManager` wraps booking state updates in a lock:
  - only one thread can check/add a slot at a time
  - this avoids race conditions and double booking
  - a tiny artificial pre-lock delay (1-5 ms) is added to simulate real-world contention

## Supported Commands

- `BOOK HH:MM-HH:MM`
  - Meaning:
    - `HH` = hour (00 to 23, 24-hour format)
    - `MM` = minute (00 to 59)
    - `HH:MM-HH:MM` = start time to end time
  - Example: `BOOK 09:00-10:00` means reserve from 9:00 AM to 10:00 AM
  - More valid examples:
    - `BOOK 00:30-01:30`
    - `BOOK 14:15-15:00`
  - Response:
    - `OK` -> booking succeeded
    - `FAIL` -> slot already booked
    - `ERROR: ...` -> invalid command or invalid slot/range
  - Rejected invalid inputs:
    - bad format (for example: `BOOK 9-10`, `BOOK 09:00/10:00`)
    - end time earlier than start time (for example: `BOOK 11:00-10:00`)
    - same start and end time (for example: `BOOK 10:00-10:00`)
- `LIST`
  - Meaning: show all currently booked slots
  - Returns all booked slots, or `EMPTY` if none
- `QUIT`
  - Meaning: disconnect this client from the server
  - Server response: `BYE`

## How To Run

Requirements:

- Python 3.11+

1. Start the server:

```bash
python server.py
```

2. In one or more other terminals, start client(s):

```bash
python client.py
```

## Stress Test

Use the stress test to simulate many concurrent clients trying to book overlapping slots.

1. Start the server first:

```bash
python server.py
```

2. In another terminal, run:

```bash
python stress_test.py
```

The script creates multiple client threads, sends `BOOK` requests for repeated slots, and prints:

- per-client result (`OK` / `FAIL`)
- summary counts per slot

## Example Session

Client A:

```text
> BOOK 09:00-10:00
[SERVER] OK
```

Client B (same slot):

```text
> BOOK 09:00-10:00
[SERVER] FAIL
```

Any client:

```text
> LIST
[SERVER] BOOKED 09:00-10:00
```

## Notes

- Booking state is in-memory only (resets when server restarts).
- No external libraries, database, or web framework is used.
