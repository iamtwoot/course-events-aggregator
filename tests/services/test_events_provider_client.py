from unittest.mock import AsyncMock, Mock

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
