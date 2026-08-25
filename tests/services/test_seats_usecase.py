import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from datetime import datetime, timedelta, timezone

from src.services.ticket_usecases import ProviderTemporarilyUnavailableError
from src.services.seats_usecase import GetFreeSeatsUsecase
from src.services.ticket_usecases import EventNotFoundError, EventNotAvailableError


def _make_fake_event(**overrides) -> Mock:
    event = Mock()
    event.id = uuid.uuid4()
    event.status = "published"
    for key, value in overrides.items():
        setattr(event, key, value)
    return event


async def test_do_returns_seats_on_success():
    fake_event = _make_fake_event()

    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock()
    fake_seats_cache.get.return_value = None

    fake_response_seats = ["A1", "A2", "A3"]
    fake_client = AsyncMock()
    fake_client.get_free_seats.return_value = {"seats": fake_response_seats}

    usecase = GetFreeSeatsUsecase(
        client = fake_client,
        events=fake_events,
        seats_cache=fake_seats_cache,
    )

    result = await usecase.do(fake_event.id)

    assert result == fake_response_seats
    fake_seats_cache.set.assert_called_once_with(str(fake_event.id), fake_response_seats)


async def test_do_raises_when_event_not_found():
    fake_event_id = uuid.uuid4()

    fake_events = AsyncMock()
    fake_events.get.return_value = None

    usecase = GetFreeSeatsUsecase(
        client=AsyncMock(),
        events=fake_events,
        seats_cache=Mock(),
    )

    with pytest.raises(EventNotFoundError):
        await usecase.do(fake_event_id)


async def test_do_raises_when_event_status_is_not_published():
    fake_event = Mock()
    fake_event.status = "new"
    fake_event.id = uuid.uuid4()

    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    usecase = GetFreeSeatsUsecase(
        client=AsyncMock(),
        events=fake_events,
        seats_cache=Mock(),
    )

    with pytest.raises(EventNotAvailableError):
        await usecase.do(fake_event.id)


async def test_do_raises_when_provider_is_not_available():
    fake_event = _make_fake_event()

    fake_events = AsyncMock()
    fake_events.get.return_value = fake_event

    fake_seats_cache = Mock()
    fake_seats_cache.get.return_value = None

    fake_client = AsyncMock()
    fake_client.get_free_seats.side_effect = httpx.HTTPStatusError(
        "500", request=Mock(), response=Mock()
    )

    usecase = GetFreeSeatsUsecase(
        client=fake_client,
        events=fake_events,
        seats_cache=fake_seats_cache,
    )

    with pytest.raises(ProviderTemporarilyUnavailableError):
        await usecase.do(fake_event.id)