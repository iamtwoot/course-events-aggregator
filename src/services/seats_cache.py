import time

from src.metrics import cache_hits_total, cache_misses_total


class SeatsCache:
    def __init__(self, ttl_seconds: int = 30):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, list[str]]] = {}

    def get(self, event_id: str) -> list[str] | None:
        entry = self._store.get(event_id)

        if entry is None:
            cache_misses_total.inc()
            return None

        cached_at, seats = entry
        if time.monotonic() - cached_at > self._ttl:
            cache_hits_total.inc()
            return None

        cache_hits_total.inc()
        return seats

    def set(self, event_id: str, seats: list[str]) -> None:
        self._store[event_id] = (time.monotonic(), seats)

    def invalidate(self, event_id: str) -> None:
        self._store.pop(event_id, None)


seats_cache = SeatsCache()
