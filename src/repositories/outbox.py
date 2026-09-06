from sqlalchemy.ext.asyncio import AsyncSession

from src.models.outbox import OutboxRecord


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def add(self, event_type: str, payload: dict) -> None:
        self._session.add(OutboxRecord(event_type=event_type, payload=payload))
