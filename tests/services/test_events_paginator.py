from unittest.mock import Mock, AsyncMock
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

