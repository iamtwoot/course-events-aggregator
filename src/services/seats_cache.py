import time


class SeatsCache:
    def __init__(self, ttl_seconds: int = 30):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, list[str]]] = {}

    def get(self, event_id: str) -> list[str] | None:
        entry = self._store.get(event_id)

        if entry is None:
            return None

        cached_at, seats = entry
        if time.monotonic() - cached_at > self._ttl:
            return None

        return seats

    def set(self, event_id: str, seats: list[str]) -> None:
        self._store[event_id] = (time.monotonic(), seats)


seats_cache = SeatsCache()
