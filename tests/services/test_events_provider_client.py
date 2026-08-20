import uuid
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.services.events_provider_client import EventsProviderClient


async def test_get_events_calls_client_with_correct_params():
    fake_response = Mock()
    fake_response.json.return_value = {
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Конференция по Python",
            }
        ],
        "next": None,
    }

    fake_client = AsyncMock()
    fake_client.get.return_value = fake_response

    client = EventsProviderClient(fake_client)

    result = await client.get_events("2000-01-01")

    fake_client.get.assert_called_once_with(
        "/api/events/",
        params={"changed_at": "2000-01-01"},
    )
    assert result == fake_response.json.return_value


async def test_get_events_raises_when_response_has_error_status():
    fake_response = Mock()
    fake_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized",
        request=Mock(),
        response=fake_response,
    )

    fake_client = AsyncMock()
    fake_client.get.return_value = fake_response

    client = EventsProviderClient(fake_client)

    with pytest.raises(httpx.HTTPStatusError):
        await client.get_events("2000-01-01")


async def test_get_events_page_responds_with_correct_params():
    fake_response = Mock()
    fake_response.json.return_value = {
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Конференция по Python",
            }
        ],
        "next": "some_url",
    }

    fake_client = AsyncMock()
    fake_client.get.return_value = fake_response

    client = EventsProviderClient(fake_client)

    result = await client.get_events_page("http://example.com/api/events/?cursor=abc")

    fake_client.get.assert_called_once_with(
        "http://example.com/api/events/?cursor=abc",
    )
    assert result == fake_response.json.return_value


async def test_get_free_seats_calls_client_with_correct_params():
    fake_response = Mock()
    fake_response.json.return_value = {
        "seats": ["A1", "A2", "A3",]
    }

    fake_client = AsyncMock()
    fake_client.get.return_value = fake_response

    client = EventsProviderClient(fake_client)

    event_id = uuid.UUID("f7479ff1-0d79-4933-a32f-5d7f76fe672d")
    result = await client.get_free_seats(event_id)

    fake_client.get.assert_called_once_with(f"/api/events/{event_id}/seats/")
    assert result == fake_response.json.return_value
