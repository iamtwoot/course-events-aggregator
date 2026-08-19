import uuid

import httpx

from src.schemas.ticket import TicketRegistration


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

    async def get_free_seats(self, event_id: uuid.UUID) -> dict[str, list[str]]:
        response = await self._client.get(
            f"/api/events/{event_id}/seats/",
        )
        response.raise_for_status()
        return response.json()

    async def register(
        self,
        event_id: uuid.UUID,
        payload: TicketRegistration,
    ) -> uuid.UUID:
        response = await self._client.post(
            f"/api/events/{event_id}/register/",
            json={
                "first_name": payload.first_name,
                "last_name": payload.last_name,
                "seat": payload.seat,
                "email": payload.email,
            },
        )
        response.raise_for_status()
        return uuid.UUID(response.json()["ticket_id"])
