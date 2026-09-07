from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.outbox import OutboxRecord, OutboxStatus


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def add(self, event_type: str, payload: dict) -> None:
        self._session.add(OutboxRecord(event_type=event_type, payload=payload))

    async def list_pending(self, limit: int) -> Sequence[OutboxRecord]:
        result = await self._session.execute(
            select(OutboxRecord)
            .where(OutboxRecord.status == OutboxStatus.PENDING)
            .order_by(OutboxRecord.created_at)
            .limit(limit)
        )
        return result.scalars().all()

    def mark_sent(self, record: OutboxRecord) -> None:
        record.status = OutboxStatus.SENT

    def mark_failed(self, record: OutboxRecord, max_attempts: int) -> None:
        record.attempts += 1
        if record.attempts >= max_attempts:
            record.status = OutboxStatus.FAILED
