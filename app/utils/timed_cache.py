from __future__ import annotations

import time
from threading import RLock
from typing import Dict, Generic, Optional, Tuple, TypeVar

T = TypeVar("T")


class TimedCache(Generic[T]):
    """
    Small in-memory cache with per-key TTL.
    Intended for data that is expensive to fetch but tolerates slight staleness.
    """

    def __init__(self, ttl_seconds: float = 30.0):
        self.ttl = float(ttl_seconds)
        self._lock = RLock()
        self._store: Dict[str, Tuple[float, T]] = {}

    def get(self, key: str) -> Optional[T]:
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if expires_at > now:
                return value
            # expired
            self._store.pop(key, None)
            return None

    def set(self, key: str, value: T) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self.ttl, value)

    def invalidate(self, key: Optional[str] = None) -> None:
        with self._lock:
            if key is None:
                self._store.clear()
            else:
                self._store.pop(key, None)
