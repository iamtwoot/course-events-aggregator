import uuid
from datetime import datetime
from typing import cast

from sqlalchemy import CursorResult, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.idempotency import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, key: str) -> IdempotencyKey | None:
        return await self._session.get(IdempotencyKey, key)

    def add(self, key: str, request_hash: str, ticket_id: uuid.UUID) -> None:
        self._session.add(
            IdempotencyKey(key=key, request_hash=request_hash, ticket_id=ticket_id)
        )

    async def delete_expired(self, older_than: datetime) -> int:
        result = cast(
            CursorResult,
            await self._session.execute(
                delete(IdempotencyKey).where(IdempotencyKey.created_at < older_than)
            ),
        )
        return result.rowcount
