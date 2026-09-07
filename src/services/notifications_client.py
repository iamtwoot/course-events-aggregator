import httpx


class NotificationsClient:
    def __init__(self, http_client: httpx.AsyncClient):
        self._client = http_client

    async def create_notification(
        self,
        message: str,
        reference_id: str,
        idempotency_key: str,
    ) -> None:
        response = await self._client.post(
            "/api/notifications",
            json={
                "message": message,
                "reference_id": reference_id,
                "idempotency_key": idempotency_key,
            },
        )
        if response.status_code == httpx.codes.CONFLICT:
            return
        response.raise_for_status()
