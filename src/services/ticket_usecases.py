import hashlib
import json
import typing
import uuid
from datetime import datetime, timezone

import httpx

from src.models.enums import EventStatus
from src.models.event import Event
from src.models.idempotency import IdempotencyKey
from src.models.ticket import Ticket
from src.schemas.ticket import TicketRegistration
from src.services.seats_pattern import is_valid_seat


class EventNotFoundError(Exception):
    pass


class EventNotAvailableError(Exception):
    pass


class InvalidSeatError(Exception):
    pass


class SeatTakenError(Exception):
    def __init__(self, detail: str = "Seat is already taken"):
        super().__init__(detail)
        self.detail = detail


class TicketNotFoundError(Exception):
    pass


class ProviderTemporarilyUnavailableError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass


class EventsProviderClientProto(typing.Protocol):
    async def get_free_seats(self, event_id: uuid.UUID) -> dict: ...

    async def register(
        self, event_id: uuid.UUID, payload: TicketRegistration
    ) -> uuid.UUID: ...

    async def unregister(self, event_id: uuid.UUID, ticket_id: uuid.UUID) -> dict: ...


class EventRepositoryProto(typing.Protocol):
    async def get(self, event_id: uuid.UUID) -> Event | None: ...


class TicketRepositoryProto(typing.Protocol):
    async def get_by_ticket_id(self, ticket_id: uuid.UUID) -> Ticket | None: ...

    def add(self, ticket_id: uuid.UUID, event_id: uuid.UUID) -> None: ...

    async def delete_by_ticket_id(self, ticket_id: uuid.UUID) -> None: ...


class SeatsCacheProto(typing.Protocol):
    def get(self, event_id: str) -> list[str] | None: ...

    def set(self, event_id: str, seats: list[str]) -> None: ...

    def invalidate(self, event_id: str) -> None: ...


class UnitOfWorkProto(typing.Protocol):
    async def commit(self) -> None: ...


class OutboxRepositoryProto(typing.Protocol):
    def add(self, event_type: str, payload: dict) -> None: ...


class IdempotencyRepositoryProto(typing.Protocol):
    async def get(self, key: str) -> IdempotencyKey | None: ...

    def add(self, key: str, request_hash: str, ticket_id: uuid.UUID) -> None: ...


def _extract_provider_detail(e: httpx.HTTPStatusError) -> str:
    try:
        body = e.response.json()
    except ValueError:
        return e.response.text
    return body.get("detail", body) if isinstance(body, dict) else body


def _request_hash(payload: TicketRegistration) -> str:
    data = payload.model_dump(mode="json", exclude={"idempotency_key"})
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


class CreateTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClientProto,
        events: EventRepositoryProto,
        tickets: TicketRepositoryProto,
        seats_cache: SeatsCacheProto,
        uow: UnitOfWorkProto,
        outbox: OutboxRepositoryProto,
        idempotency: IdempotencyRepositoryProto,
    ):
        self._client = client
        self._events = events
        self._tickets = tickets
        self._seats_cache = seats_cache
        self._uow = uow
        self._outbox = outbox
        self._idempotency = idempotency

    async def do(self, payload: TicketRegistration) -> uuid.UUID:
        request_hash = ""
        if payload.idempotency_key:
            request_hash = _request_hash(payload)
            existing = await self._idempotency.get(payload.idempotency_key)
            if existing:
                if existing.request_hash != request_hash:
                    raise IdempotencyConflictError
                return existing.ticket_id

        event = await self._events.get(payload.event_id)
        if event is None:
            raise EventNotFoundError

        if event.status != EventStatus.PUBLISHED:
            raise EventNotAvailableError("Event is not published")

        if event.registration_deadline < datetime.now(timezone.utc):
            raise EventNotAvailableError("Registration is closed")

        if event.place_seats_pattern is None or not is_valid_seat(
            event.place_seats_pattern, payload.seat
        ):
            raise InvalidSeatError

        available_seats = self._seats_cache.get(str(event.id))
        if available_seats is None:
            try:
                raw = await self._client.get_free_seats(event.id)
            except httpx.HTTPStatusError as e:
                raise ProviderTemporarilyUnavailableError from e
            available_seats = raw["seats"]
            self._seats_cache.set(str(event.id), available_seats)

        if payload.seat not in available_seats:
            raise SeatTakenError

        try:
            ticket_id = await self._client.register(event.id, payload)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise SeatTakenError(_extract_provider_detail(e)) from e
            raise

        available_seats.remove(payload.seat)
        self._seats_cache.set(str(event.id), available_seats)

        self._tickets.add(ticket_id=ticket_id, event_id=event.id)
        self._outbox.add(
            event_type="ticket.purchased",
            payload={"ticket_id": str(ticket_id), "event_name": event.name},
        )
        if payload.idempotency_key:
            self._idempotency.add(
                key=payload.idempotency_key,
                request_hash=request_hash,
                ticket_id=ticket_id,
            )
        await self._uow.commit()
        return ticket_id


class CancelTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClientProto,
        tickets: TicketRepositoryProto,
        seats_cache: SeatsCacheProto,
        uow: UnitOfWorkProto,
    ):
        self._client = client
        self._tickets = tickets
        self._seats_cache = seats_cache
        self._uow = uow

    async def do(self, ticket_id: uuid.UUID) -> None:
        ticket = await self._tickets.get_by_ticket_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError

        event_id = ticket.event_id

        try:
            await self._client.unregister(event_id, ticket_id)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise TicketNotFoundError from e
            raise

        self._seats_cache.invalidate(str(event_id))

        await self._tickets.delete_by_ticket_id(ticket_id)
        await self._uow.commit()
