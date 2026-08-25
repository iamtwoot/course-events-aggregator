import typing
import uuid

import httpx

from src.models.enums import EventStatus
from src.models.event import Event
from src.services.ticket_usecases import (
    EventNotAvailableError,
    EventNotFoundError,
    ProviderTemporarilyUnavailableError,
)


class EventsProviderClientProto(typing.Protocol):
    async def get_free_seats(self, event_id: uuid.UUID) -> dict: ...


class EventRepositoryProto(typing.Protocol):
    async def get(self, event_id: uuid.UUID) -> Event | None: ...


class SeatsCacheProto(typing.Protocol):
    def get(self, event_id: str) -> list[str] | None: ...
    def set(self, event_id: str, seats: list[str]) -> None: ...


class GetFreeSeatsUsecase:
    def __init__(
        self,
        client: EventsProviderClientProto,
        events: EventRepositoryProto,
        seats_cache: SeatsCacheProto,
    ):
        self._client = client
        self._events = events
        self._seats_cache = seats_cache

    async def do(self, event_id: uuid.UUID) -> list[str]:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFoundError

        if event.status != EventStatus.PUBLISHED:
            raise EventNotAvailableError("Event is not published")

        seats = self._seats_cache.get(str(event.id))
        if seats is None:
            try:
                raw = await self._client.get_free_seats(event.id)
            except httpx.HTTPStatusError as e:
                raise ProviderTemporarilyUnavailableError from e
            seats = raw["seats"]
            self._seats_cache.set(str(event.id), seats)

        return seats
