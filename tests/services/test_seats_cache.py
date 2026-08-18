from src.services.seats_cache import SeatsCache


def test_cache_returns_none_when_empty():
    cache = SeatsCache()
    assert cache.get("some-id") is None


def test_cache_returns_value_after_set():
    cache = SeatsCache()
    cache.set("some-id", ["A1", "A2"])
    assert cache.get("some-id") == ["A1", "A2"]


def test_cache_expires_after_ttl():
    cache = SeatsCache(ttl_seconds=0)
    cache.set("some-id", ["A1", "A2"])
    assert cache.get("some-id") is None
