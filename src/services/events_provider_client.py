import time
import uuid

import httpx

from src.metrics import (
    events_provider_requests_duration_seconds,
    events_provider_requests_total,
)
from src.schemas.ticket import TicketRegistration


class EventsProviderClient:
    def __init__(self, http_client: httpx.AsyncClient):
        self._client = http_client

    async def _request(
        self,
        method: str,
        url: str,
        *,
        endpoint: str,
        **kwargs,
    ) -> httpx.Response:
        start_time = time.monotonic()
        try:
            response = await self._client.request(method, url, **kwargs)
        except httpx.HTTPError:
            events_provider_requests_total.labels(
                endpoint=endpoint,
                status="error",
            ).inc()
            raise
        finally:
            events_provider_requests_duration_seconds.labels(
                endpoint=endpoint,
            ).observe(time.monotonic() - start_time)

        events_provider_requests_total.labels(
            endpoint=endpoint,
            status=response.status_code,
        ).inc()
        response.raise_for_status()
        return response

    async def get_events(self, changed_at: str) -> dict:
        response = await self._request(
            "GET",
            "/api/events/",
            endpoint="/events",
            params={"changed_at": changed_at},
        )
        return response.json()

    async def get_events_page(self, url: str) -> dict:
        response = await self._request("GET", url, endpoint="/events")
        return response.json()

    async def get_free_seats(self, event_id: uuid.UUID) -> dict[str, list[str]]:
        response = await self._request(
            "GET",
            f"/api/events/{event_id}/seats/",
            endpoint="/seats",
        )
        return response.json()

    async def register(
        self,
        event_id: uuid.UUID,
        payload: TicketRegistration,
    ) -> uuid.UUID:
        response = await self._request(
            "POST",
            f"/api/events/{event_id}/register/",
            endpoint="/registration",
            json={
                "first_name": payload.first_name,
                "last_name": payload.last_name,
                "seat": payload.seat,
                "email": payload.email,
            },
        )
        return uuid.UUID(response.json()["ticket_id"])

    async def unregister(
        self,
        event_id: uuid.UUID,
        ticket_id: uuid.UUID,
    ):
        response = await self._request(
            "DELETE",
            f"/api/events/{event_id}/unregister/",
            endpoint="/unregister",
            json={
                "ticket_id": str(ticket_id),
            },
        )
        return response.json()
