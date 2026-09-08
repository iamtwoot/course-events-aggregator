import json

import httpx
import pytest

from src.services.notifications_client import NotificationsClient


def _client(handler) -> NotificationsClient:
    transport = httpx.MockTransport(handler)
    return NotificationsClient(
        httpx.AsyncClient(transport=transport, base_url="http://capashino.test")
    )


async def test_conflict_is_treated_as_success():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"detail": "already exists"})

    await _client(handler).create_notification(
        message="text", reference_id="T1", idempotency_key="K1"
    )


async def test_server_error_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    with pytest.raises(httpx.HTTPStatusError):
        await _client(handler).create_notification(
            message="test", reference_id="T1", idempotency_key="K1"
        )


async def test_sends_expected_body():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.read().decode()
        return httpx.Response(201, json={"id": "N1"})

    await _client(handler).create_notification(
        message="Вы успешно зарегистрированы", reference_id="T1", idempotency_key="K1"
    )

    body = json.loads(captured["body"])

    assert captured["url"].endswith("/api/notifications")
    assert body["idempotency_key"] == "K1"
    assert body["reference_id"] == "T1"
    assert body["message"] == "Вы успешно зарегистрированы"
