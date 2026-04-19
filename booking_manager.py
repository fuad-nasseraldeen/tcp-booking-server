"""Thread-safe in-memory booking storage for time slots."""

from __future__ import annotations

import random
import re
import threading
import time
from typing import Final


_SLOT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$")
_DELAY_MIN_SECONDS: Final[float] = 0.001
_DELAY_MAX_SECONDS: Final[float] = 0.005
_DELAY_RANDOM_SEED: Final[int] = 42


class BookingManager:
    """Stores booked time slots safely across threads."""

    def __init__(self) -> None:
        self._booked_slots: set[str] = set()
        self._lock = threading.Lock()
        self._delay_lock = threading.Lock()
        self._rng = random.Random(_DELAY_RANDOM_SEED)

    def book_slot(self, slot: str) -> bool:
        """Try to book a slot.

        Returns True when booking succeeds and False when already taken.
        Raises ValueError when slot value is invalid.
        """
        normalized_slot = slot.strip()
        self.validate_slot(normalized_slot)

        # Small artificial jitter to simulate network and processing variance.
        delay_seconds = self._next_delay()
        time.sleep(delay_seconds)

        with self._lock:
            if normalized_slot in self._booked_slots:
                return False
            self._booked_slots.add(normalized_slot)
            return True

    def is_valid_slot(self, slot: str) -> bool:
        """Validate slot format (for example: 09:00-10:00)."""
        return bool(_SLOT_PATTERN.fullmatch(slot))

    def validate_slot(self, slot: str) -> None:
        """Validate slot format and time range."""
        if not self.is_valid_slot(slot):
            raise ValueError("Invalid slot format. Use HH:MM-HH:MM (24-hour).")

        start_text, end_text = slot.split("-", maxsplit=1)
        start_minutes = self._to_minutes(start_text)
        end_minutes = self._to_minutes(end_text)

        if start_minutes == end_minutes:
            raise ValueError("Invalid time range. Start and end times cannot be the same.")
        if end_minutes < start_minutes:
            raise ValueError("Invalid time range. End time must be later than start time.")

    def _to_minutes(self, time_text: str) -> int:
        """Convert HH:MM to total minutes."""
        hour_text, minute_text = time_text.split(":", maxsplit=1)
        return int(hour_text) * 60 + int(minute_text)

    def _next_delay(self) -> float:
        """Get deterministic pseudo-random delay in seconds."""
        with self._delay_lock:
            return self._rng.uniform(_DELAY_MIN_SECONDS, _DELAY_MAX_SECONDS)

    def list_slots(self) -> list[str]:
        """Return all booked slots sorted by time."""
        with self._lock:
            return sorted(self._booked_slots)
