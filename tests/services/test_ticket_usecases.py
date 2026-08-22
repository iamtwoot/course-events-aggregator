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
    InvalidSeatError,
    ProviderTemporarilyUnavailableError,
    SeatTakenError,
    TicketNotFoundError,
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

    fake_events = AsyncMock()
    fake_events.get.return_value = None

    usecase = CreateTicketUsecase(
        client=AsyncMock(),
        events=fake_events,
        tickets=AsyncMock(),
        seats_cache=Mock(),
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

    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    usecase = CreateTicketUsecase(
        client=AsyncMock(),
        events=fake_events,
        tickets=AsyncMock(),
        seats_cache=Mock(),
    )

    with pytest.raises(EventNotAvailableError):
        await usecase.do(payload)


async def test_do_raises_when_registration_deadline_passed():
    payload = _make_payload()
    fake_event = _make_fake_event(
        id=payload.event_id,
        registration_deadline=datetime.now(timezone.utc) - timedelta(days=1),
    )
    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    usecase = CreateTicketUsecase(
        client=AsyncMock(), events=fake_events, tickets=AsyncMock(), seats_cache=Mock()
    )

    with pytest.raises(EventNotAvailableError):
        await usecase.do(payload)


async def test_do_raises_when_seat_does_not_exist_in_pattern():
    payload = _make_payload(seat="Z999")
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    usecase = CreateTicketUsecase(
        client=AsyncMock(), events=fake_events, tickets=AsyncMock(), seats_cache=Mock()
    )

    with pytest.raises(InvalidSeatError):
        await usecase.do(payload)


async def test_do_raises_when_provider_seats_lookup_fails():
    payload = _make_payload()
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock()
    fake_seats_cache.get.return_value = None

    fake_client = AsyncMock()
    fake_client.get_free_seats.side_effect = httpx.HTTPStatusError(
        "500", request=Mock(), response=Mock()
    )

    usecase = CreateTicketUsecase(
        client=fake_client, events=fake_events, tickets=AsyncMock(), seats_cache=fake_seats_cache
    )

    with pytest.raises(ProviderTemporarilyUnavailableError):
        await usecase.do(payload)


async def test_do_raises_when_seat_is_taken_according_to_cache():
    payload = _make_payload(seat="A15")
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock()
    fake_seats_cache.get.return_value = ["A1", "A2"]

    usecase = CreateTicketUsecase(
        client=AsyncMock(), events=fake_events, tickets=AsyncMock(), seats_cache=fake_seats_cache
    )

    with pytest.raises(SeatTakenError):
        await usecase.do(payload)


async def test_do_raises_seat_taken_when_provider_rejects_registration():
    payload = _make_payload(seat="A15")
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock()
    fake_seats_cache.get.return_value = ["A15"]

    fake_provider_response = Mock()
    fake_provider_response.status_code = 400
    fake_provider_response.json.return_value = {"detail": "Seat already sold"}

    fake_client = AsyncMock()
    fake_client.register.side_effect = httpx.HTTPStatusError(
        "400", request=Mock(), response=fake_provider_response
    )

    usecase = CreateTicketUsecase(
        client=fake_client, events=fake_events, tickets=AsyncMock(), seats_cache=fake_seats_cache
    )

    with pytest.raises(SeatTakenError) as exc_info:
        await usecase.do(payload)

    assert exc_info.value.detail == "Seat already sold"


async def test_do_reraises_when_provider_registration_fails_unexpectedly():
    payload = _make_payload(seat="A15")
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock()
    fake_seats_cache.get.return_value = ["A15"]

    fake_provider_response = Mock()
    fake_provider_response.status_code = 500

    fake_client = AsyncMock()
    fake_client.register.side_effect = httpx.HTTPStatusError(
        "500", request=Mock(), response=fake_provider_response
    )

    usecase = CreateTicketUsecase(
        client=fake_client, events=fake_events, tickets=AsyncMock(), seats_cache=fake_seats_cache
    )

    with pytest.raises(httpx.HTTPStatusError):
        await usecase.do(payload)


async def test_do_creates_ticket_on_success():
    payload = _make_payload(seat="A15")
    fake_event = _make_fake_event(id=payload.event_id)
    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock()
    fake_seats_cache.get.return_value = ["A15", "A16"]

    fake_ticket_id = uuid.uuid4()
    fake_client = AsyncMock()
    fake_client.register.return_value = fake_ticket_id

    fake_tickets = AsyncMock()

    usecase = CreateTicketUsecase(
        client=fake_client, events=fake_events, tickets=fake_tickets, seats_cache=fake_seats_cache
    )

    result = await usecase.do(payload)

    assert result == fake_ticket_id
    fake_tickets.create.assert_called_once_with(ticket_id=fake_ticket_id, event_id=fake_event.id)


async def test_cancel_raises_when_ticket_not_found():
    fake_tickets = AsyncMock()
    fake_tickets.get_by_ticket_id.return_value = None

    usecase = CancelTicketUsecase(client=AsyncMock(), tickets=fake_tickets, seats_cache=Mock())

    with pytest.raises(TicketNotFoundError):
        await usecase.do(uuid.uuid4())


async def test_cancel_raises_when_provider_reports_ticket_not_found():
    fake_ticket = Mock()
    fake_ticket.event_id = uuid.uuid4()
    fake_tickets = AsyncMock()
    fake_tickets.get_by_ticket_id.return_value = fake_ticket

    fake_response = Mock()
    fake_response.status_code = 404
    fake_client = AsyncMock()
    fake_client.unregister.side_effect = httpx.HTTPStatusError(
        "404", request=Mock(), response=fake_response
    )

    usecase = CancelTicketUsecase(client=fake_client, tickets=fake_tickets, seats_cache=Mock())

    with pytest.raises(TicketNotFoundError):
        await usecase.do(uuid.uuid4())


async def test_cancel_reraises_when_provider_fails_unexpectedly():
    fake_ticket = Mock()
    fake_ticket.event_id = uuid.uuid4()
    fake_tickets = AsyncMock()
    fake_tickets.get_by_ticket_id.return_value = fake_ticket

    fake_response = Mock()
    fake_response.status_code = 500
    fake_client = AsyncMock()
    fake_client.unregister.side_effect = httpx.HTTPStatusError(
        "500", request=Mock(), response=fake_response
    )

    usecase = CancelTicketUsecase(client=fake_client, tickets=fake_tickets, seats_cache=Mock())

    with pytest.raises(httpx.HTTPStatusError):
        await usecase.do(uuid.uuid4())


async def test_cancel_deletes_ticket_and_invalidates_cache_on_success():
    fake_event_id = uuid.uuid4()
    fake_ticket_id = uuid.uuid4()

    fake_ticket = Mock()
    fake_ticket.event_id = fake_event_id
    fake_tickets = AsyncMock()
    fake_tickets.get_by_ticket_id.return_value = fake_ticket

    fake_seats_cache = Mock()

    usecase = CancelTicketUsecase(
        client=AsyncMock(), tickets=fake_tickets, seats_cache=fake_seats_cache
    )

    await usecase.do(fake_ticket_id)

    fake_tickets.delete_by_ticket_id.assert_called_once_with(fake_ticket_id)
    fake_seats_cache.invalidate.assert_called_once_with(str(fake_event_id))
