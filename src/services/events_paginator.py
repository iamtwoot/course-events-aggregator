from .events_provider_client import EventsProviderClient


class EventsPaginator:
    def __init__(self, client: EventsProviderClient, changed_at: str):
        self._client = client
        self._changed_at = changed_at
        self._buffer: list[dict] = []
        self._next_url: str | None = None
        self._started = False

    def __aiter__(self):
        return self

    async def __anext__(self) -> dict:
        if not self._buffer:
            if not self._started:
                page = await self._client.get_events(self._changed_at)
                self._started = True
            elif self._next_url:
                page = await self._client.get_events_page(self._next_url)
            else:
                raise StopAsyncIteration

            self._buffer = page["results"]
            self._next_url = page["next"]

        if not self._buffer:
            raise StopAsyncIteration

        return self._buffer.pop(0)
