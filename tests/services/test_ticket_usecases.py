import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from src.schemas.ticket import TicketRegistration
from src.services.ticket_usecases import CreateTicketUsecase, EventNotFoundError, EventNotAvailableError


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
        client=AsyncMock(), events=fake_events, tickets=AsyncMock(), seats_cache=Mock(),
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
        client=AsyncMock(), events=fake_events, tickets=AsyncMock(), seats_cache=Mock(),
    )

    with pytest.raises(EventNotAvailableError):
        await usecase.do(payload)



