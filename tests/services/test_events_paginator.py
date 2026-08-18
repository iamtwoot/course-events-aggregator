from unittest.mock import AsyncMock, Mock

from src.services.events_paginator import EventsPaginator
from src.services.events_provider_client import EventsProviderClient


async def test_paginator_gets_empty_result():
    fake_response = Mock()
    fake_response.json.return_value = {
        "results": [],
        "next": None,
    }

    fake_client = AsyncMock()
    fake_client.get.return_value = fake_response

    client = EventsProviderClient(fake_client)
    paginator = EventsPaginator(client, changed_at="2000-01-01")

    results = [event async for event in paginator]

    assert results == []


async def test_paginator_returns_events():
    event1 = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Конференция по Python",
    }
    event2 = {"id": "650e8400-e29b-41d4-a716-446655440001", "name": "Митап по FastAPI"}

    fake_response1 = Mock()
    fake_response1.json.return_value = {
        "results": [event1],
        "next": "url_for_the_next_page",
    }

    fake_response2 = Mock()
    fake_response2.json.return_value = {"results": [event2], "next": None}

    fake_client = AsyncMock()
    fake_client.get.side_effect = [fake_response1, fake_response2]

    client = EventsProviderClient(fake_client)
    paginator = EventsPaginator(client, changed_at="2000-01-01")

    results = [event async for event in paginator]

    assert results == [event1, event2]
