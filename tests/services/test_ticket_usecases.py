import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.schemas.ticket import TicketRegistration
from src.services.ticket_usecases import (
    CancelTicketUsecase,
    CreateTicketUsecase,
    EventNotAvailableError,
    EventNotFoundError,
    EventRepositoryProto,
    EventsProviderClientProto,
    IdempotencyConflictError,
    IdempotencyRepositoryProto,
    InvalidSeatError,
    OutboxRepositoryProto,
    ProviderTemporarilyUnavailableError,
    SeatsCacheProto,
    SeatTakenError,
    TicketNotFoundError,
    TicketRepositoryProto,
    UnitOfWorkProto,
    _request_hash,
)


def _make_payload(**overrides) -> TicketRegistration:
    defaults = dict(
        event_id=uuid.uuid4(),
        first_name="Ivan",
        last_name="Ivanov",
        email="example@example.com",
        seat="A15",
    )
    defaults.update(overrides)
    return TicketRegistration(**defaults)


def _make_fake_event(**overrides) -> Mock:
    event = Mock()
    event.id = uuid.uuid4()
    event.status = "published"
    event.registration_deadline = datetime.now(timezone.utc) + timedelta(days=1)
    event.place_seats_pattern = "A1-1000"
    for key, value in overrides.items():
        setattr(event, key, value)
    return event


async def test_do_raises_when_event_not_found():
    payload = TicketRegistration(
        event_id=uuid.uuid4(),
        first_name="Ivan",
        last_name="Ivanov",
        email="example@example.com",
        seat="A15",
    )

    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_events.get.return_value = None

    usecase = CreateTicketUsecase(
        client=AsyncMock(spec=EventsProviderClientProto),
        events=fake_events,
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=Mock(spec=SeatsCacheProto),
        uow=AsyncMock(spec=UnitOfWorkProto),
        outbox=Mock(spec=OutboxRepositoryProto),
        idempotency=AsyncMock(spec=IdempotencyRepositoryProto),
    )

    with pytest.raises(EventNotFoundError):
        await usecase.do(payload)


async def test_do_raises_when_status_not_published():
    payload = TicketRegistration(
        event_id=uuid.uuid4(),
        first_name="Ivan",
        last_name="Ivanov",
        email="example@example.com",
        seat="A15",
    )

    fake_event = Mock()
    fake_event.status = "new"

    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_events.get.return_value = fake_event

    usecase = CreateTicketUsecase(
        client=AsyncMock(spec=EventsProviderClientProto),
        events=fake_events,
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=Mock(spec=SeatsCacheProto),
        uow=AsyncMock(spec=UnitOfWorkProto),
        outbox=Mock(spec=OutboxRepositoryProto),
        idempotency=AsyncMock(spec=IdempotencyRepositoryProto),
    )

    with pytest.raises(EventNotAvailableError):
        await usecase.do(payload)


async def test_do_raises_when_registration_deadline_passed():
    payload = _make_payload()
    fake_event = _make_fake_event(
        id=payload.event_id,
        registration_deadline=datetime.now(timezone.utc) - timedelta(days=1),
    )
    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_events.get.return_value = fake_event

    usecase = CreateTicketUsecase(
        client=AsyncMock(spec=EventsProviderClientProto),
        events=fake_events,
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=Mock(spec=SeatsCacheProto),
        uow=AsyncMock(spec=UnitOfWorkProto),
        outbox=Mock(spec=OutboxRepositoryProto),
        idempotency=AsyncMock(spec=IdempotencyRepositoryProto),
    )

    with pytest.raises(EventNotAvailableError):
        await usecase.do(payload)


async def test_do_raises_when_seat_does_not_exist_in_pattern():
    payload = _make_payload(seat="Z999")
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_events.get.return_value = fake_event

    usecase = CreateTicketUsecase(
        client=AsyncMock(spec=EventsProviderClientProto),
        events=fake_events,
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=Mock(spec=SeatsCacheProto),
        uow=AsyncMock(spec=UnitOfWorkProto),
        outbox=Mock(spec=OutboxRepositoryProto),
        idempotency=AsyncMock(spec=IdempotencyRepositoryProto),
    )

    with pytest.raises(InvalidSeatError):
        await usecase.do(payload)


async def test_do_raises_when_provider_seats_lookup_fails():
    payload = _make_payload()
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock(spec=SeatsCacheProto)
    fake_seats_cache.get.return_value = None

    fake_client = AsyncMock(spec=EventsProviderClientProto)
    fake_client.get_free_seats.side_effect = httpx.HTTPStatusError(
        "500", request=Mock(), response=Mock()
    )

    usecase = CreateTicketUsecase(
        client=fake_client,
        events=fake_events,
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=fake_seats_cache,
        uow=AsyncMock(spec=UnitOfWorkProto),
        outbox=Mock(spec=OutboxRepositoryProto),
        idempotency=AsyncMock(spec=IdempotencyRepositoryProto),
    )

    with pytest.raises(ProviderTemporarilyUnavailableError):
        await usecase.do(payload)


async def test_do_raises_when_seat_is_taken_according_to_cache():
    payload = _make_payload(seat="A15")
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock(spec=SeatsCacheProto)
    fake_seats_cache.get.return_value = ["A1", "A2"]

    usecase = CreateTicketUsecase(
        client=AsyncMock(spec=EventsProviderClientProto),
        events=fake_events,
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=fake_seats_cache,
        uow=AsyncMock(spec=UnitOfWorkProto),
        outbox=Mock(spec=OutboxRepositoryProto),
        idempotency=AsyncMock(spec=IdempotencyRepositoryProto),
    )

    with pytest.raises(SeatTakenError):
        await usecase.do(payload)


async def test_do_raises_seat_taken_when_provider_rejects_registration():
    payload = _make_payload(seat="A15")
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock(spec=SeatsCacheProto)
    fake_seats_cache.get.return_value = ["A15"]

    fake_provider_response = Mock()
    fake_provider_response.status_code = 400
    fake_provider_response.json.return_value = {"detail": "Seat already sold"}

    fake_client = AsyncMock(spec=EventsProviderClientProto)
    fake_client.register.side_effect = httpx.HTTPStatusError(
        "400", request=Mock(), response=fake_provider_response
    )

    fake_outbox = Mock(spec=OutboxRepositoryProto)

    usecase = CreateTicketUsecase(
        client=fake_client,
        events=fake_events,
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=fake_seats_cache,
        uow=AsyncMock(spec=UnitOfWorkProto),
        outbox=fake_outbox,
        idempotency=AsyncMock(spec=IdempotencyRepositoryProto),
    )

    with pytest.raises(SeatTakenError) as exc_info:
        await usecase.do(payload)

    assert exc_info.value.detail == "Seat already sold"
    fake_outbox.add.assert_not_called()


async def test_do_reraises_when_provider_registration_fails_unexpectedly():
    payload = _make_payload(seat="A15")
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock(spec=SeatsCacheProto)
    fake_seats_cache.get.return_value = ["A15"]

    fake_provider_response = Mock()
    fake_provider_response.status_code = 500

    fake_client = AsyncMock(spec=EventsProviderClientProto)
    fake_client.register.side_effect = httpx.HTTPStatusError(
        "500", request=Mock(), response=fake_provider_response
    )

    fake_outbox = Mock(spec=OutboxRepositoryProto)

    usecase = CreateTicketUsecase(
        client=fake_client,
        events=fake_events,
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=fake_seats_cache,
        uow=AsyncMock(spec=UnitOfWorkProto),
        outbox=fake_outbox,
        idempotency=AsyncMock(spec=IdempotencyRepositoryProto),
    )

    with pytest.raises(httpx.HTTPStatusError):
        await usecase.do(payload)
    fake_outbox.add.assert_not_called()


async def test_do_creates_ticket_on_success():
    payload = _make_payload(seat="A15")
    fake_event = _make_fake_event(id=payload.event_id, name="fake_name")
    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock(spec=SeatsCacheProto)
    fake_seats_cache.get.return_value = ["A15", "A16"]

    fake_ticket_id = uuid.uuid4()
    fake_client = AsyncMock(spec=EventsProviderClientProto)
    fake_client.register.return_value = fake_ticket_id

    fake_tickets = Mock(spec=TicketRepositoryProto)

    fake_uow = AsyncMock(spec=UnitOfWorkProto)

    fake_outbox = Mock(spec=OutboxRepositoryProto)

    usecase = CreateTicketUsecase(
        client=fake_client,
        events=fake_events,
        tickets=fake_tickets,
        seats_cache=fake_seats_cache,
        uow=fake_uow,
        outbox=fake_outbox,
        idempotency=AsyncMock(spec=IdempotencyRepositoryProto),
    )

    result = await usecase.do(payload)

    assert result == fake_ticket_id
    fake_tickets.add.assert_called_once_with(
        ticket_id=fake_ticket_id, event_id=fake_event.id
    )
    fake_uow.commit.assert_awaited_once()
    fake_outbox.add.assert_called_once_with(
        event_type="ticket.purchased",
        payload={"ticket_id": str(fake_ticket_id), "event_name": fake_event.name},
    )


async def test_do_returns_saved_ticket_on_repeated_key():
    payload = _make_payload(seat="A15", idempotency_key="K1")

    fake_ticket_id = uuid.uuid4()
    saved = Mock()
    saved.request_hash = _request_hash(payload)
    saved.ticket_id = fake_ticket_id

    fake_idempotency = AsyncMock(spec=IdempotencyRepositoryProto)
    fake_idempotency.get.return_value = saved

    fake_client = AsyncMock(spec=EventsProviderClientProto)
    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_outbox = Mock(spec=OutboxRepositoryProto)
    fake_ouw = AsyncMock(spec=UnitOfWorkProto)

    usecase = CreateTicketUsecase(
        client=fake_client,
        events=fake_events,
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=Mock(spec=SeatsCacheProto),
        uow=fake_ouw,
        outbox=fake_outbox,
        idempotency=fake_idempotency,
    )

    result = await usecase.do(payload)

    assert result == fake_ticket_id
    fake_client.register.assert_not_awaited()
    fake_events.get.assert_not_awaited()
    fake_outbox.add.assert_not_called()
    fake_ouw.commit.assert_not_awaited()


async def test_do_raises_conflict_when_hash_differs():
    payload = _make_payload(seat="A15", idempotency_key="K1")

    saved = Mock()
    saved.request_hash = "different_hash"
    saved.ticket_id = uuid.uuid4()

    fake_idempotency = AsyncMock(spec=IdempotencyRepositoryProto)
    fake_idempotency.get.return_value = saved

    fake_client = AsyncMock(spec=EventsProviderClientProto)
    fake_outbox = Mock(spec=OutboxRepositoryProto)

    fake_uow = AsyncMock(spec=UnitOfWorkProto)

    usecase = CreateTicketUsecase(
        client=fake_client,
        events=AsyncMock(spec=EventRepositoryProto),
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=Mock(spec=SeatsCacheProto),
        uow=fake_uow,
        outbox=fake_outbox,
        idempotency=fake_idempotency,
    )

    with pytest.raises(IdempotencyConflictError):
        await usecase.do(payload)

    fake_client.register.assert_not_awaited()
    fake_outbox.add.assert_not_called()
    fake_uow.commit.assert_not_called()


async def test_do_saves_idempotency_key_on_success():
    payload = _make_payload(seat="A15", idempotency_key="K1")
    fake_event = _make_fake_event(id=payload.event_id, name="fake_name")

    fake_events = AsyncMock(spec=EventRepositoryProto)
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock(spec=SeatsCacheProto)
    fake_seats_cache.get.return_value = ["A15", "A16"]

    fake_ticket_id = uuid.uuid4()
    fake_client = AsyncMock(spec=EventsProviderClientProto)
    fake_client.register.return_value = fake_ticket_id

    fake_idempotency = AsyncMock(spec=IdempotencyRepositoryProto)
    fake_idempotency.get.return_value = None

    usecase = CreateTicketUsecase(
        client=fake_client,
        events=fake_events,
        tickets=Mock(spec=TicketRepositoryProto),
        seats_cache=fake_seats_cache,
        uow=AsyncMock(spec=UnitOfWorkProto),
        outbox=Mock(spec=OutboxRepositoryProto),
        idempotency=fake_idempotency,
    )

    result = await usecase.do(payload)

    assert result == fake_ticket_id
    fake_idempotency.add.assert_called_once_with(
        key="K1",
        request_hash=_request_hash(payload),
        ticket_id=fake_ticket_id,
    )


async def test_cancel_raises_when_ticket_not_found():
    fake_tickets = AsyncMock(spec=TicketRepositoryProto)
    fake_tickets.get_by_ticket_id.return_value = None

    usecase = CancelTicketUsecase(
        client=AsyncMock(spec=EventsProviderClientProto),
        tickets=fake_tickets,
        seats_cache=Mock(spec=SeatsCacheProto),
        uow=AsyncMock(spec=UnitOfWorkProto),
    )

    with pytest.raises(TicketNotFoundError):
        await usecase.do(uuid.uuid4())


async def test_cancel_raises_when_provider_reports_ticket_not_found():
    fake_ticket = Mock()
    fake_ticket.event_id = uuid.uuid4()
    fake_tickets = AsyncMock(spec=TicketRepositoryProto)
    fake_tickets.get_by_ticket_id.return_value = fake_ticket

    fake_response = Mock()
    fake_response.status_code = 404
    fake_client = AsyncMock(spec=EventsProviderClientProto)
    fake_client.unregister.side_effect = httpx.HTTPStatusError(
        "404", request=Mock(), response=fake_response
    )

    usecase = CancelTicketUsecase(
        client=fake_client,
        tickets=fake_tickets,
        seats_cache=Mock(spec=SeatsCacheProto),
        uow=AsyncMock(spec=UnitOfWorkProto),
    )

    with pytest.raises(TicketNotFoundError):
        await usecase.do(uuid.uuid4())


async def test_cancel_reraises_when_provider_fails_unexpectedly():
    fake_ticket = Mock()
    fake_ticket.event_id = uuid.uuid4()
    fake_tickets = AsyncMock(spec=TicketRepositoryProto)
    fake_tickets.get_by_ticket_id.return_value = fake_ticket

    fake_response = Mock()
    fake_response.status_code = 500
    fake_client = AsyncMock(spec=EventsProviderClientProto)
    fake_client.unregister.side_effect = httpx.HTTPStatusError(
        "500", request=Mock(), response=fake_response
    )

    usecase = CancelTicketUsecase(
        client=fake_client,
        tickets=fake_tickets,
        seats_cache=Mock(spec=SeatsCacheProto),
        uow=AsyncMock(spec=UnitOfWorkProto),
    )

    with pytest.raises(httpx.HTTPStatusError):
        await usecase.do(uuid.uuid4())


async def test_cancel_deletes_ticket_and_invalidates_cache_on_success():
    fake_event_id = uuid.uuid4()
    fake_ticket_id = uuid.uuid4()

    fake_ticket = Mock()
    fake_ticket.event_id = fake_event_id
    fake_tickets = AsyncMock(spec=TicketRepositoryProto)
    fake_tickets.get_by_ticket_id.return_value = fake_ticket

    fake_seats_cache = Mock(spec=SeatsCacheProto)

    usecase = CancelTicketUsecase(
        client=AsyncMock(spec=EventsProviderClientProto),
        tickets=fake_tickets,
        seats_cache=fake_seats_cache,
        uow=AsyncMock(spec=UnitOfWorkProto),
    )

    await usecase.do(fake_ticket_id)

    fake_tickets.delete_by_ticket_id.assert_called_once_with(fake_ticket_id)
    fake_seats_cache.invalidate.assert_called_once_with(str(fake_event_id))
