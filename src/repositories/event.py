from sqlalchemy.ext.asyncio import AsyncSession

from src.models.event import Event


class EventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert(self, event: Event):
        await self._session.merge(event)
