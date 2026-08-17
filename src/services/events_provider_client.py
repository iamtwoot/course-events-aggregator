import httpx


class EventsProviderClient:
    def __init__(self, http_client: httpx.AsyncClient):
        self._client = http_client

    async def get_events(self, changed_at: str) -> dict:
        response = await self._client.get(
            "/api/events/", params={"changed_at": changed_at}
        )
        response.raise_for_status()
        return response.json()

    async def get_events_page(self, url: str) -> dict:
        response = await self._client.get(url)
        response.raise_for_status()
        return response.json()
