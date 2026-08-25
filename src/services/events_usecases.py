import typing
import uuid
from datetime import date

from src.models.event import Event
from src.services.ticket_usecases import EventNotFoundError


class EventRepositoryProto(typing.Protocol):
    async def list(
        self,
        *,
        date_from: date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Event], int]: ...

    async def get(self, event_id: uuid.UUID) -> Event | None: ...


class ListEventsUsecase:
    def __init__(self, events: EventRepositoryProto):
        self._events = events

    async def do(
        self,
        *,
        date_from: date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Event], int, bool]:
        events, total = await self._events.list(
            date_from=date_from,
            page=page,
            page_size=page_size,
        )
        has_next = page * page_size < total
        return events, total, has_next


class GetEventUsecase:
    def __init__(self, events: EventRepositoryProto):
        self._events = events

    async def do(self, event_id: uuid.UUID) -> Event:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFoundError
        return event
