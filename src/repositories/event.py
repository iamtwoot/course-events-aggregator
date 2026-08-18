import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.event import Event


class EventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert(self, event: Event):
        await self._session.merge(event)

    async def list(
            self,
            *,
            date_from: date | None,
            page: int,
            page_size: int,
    ) -> tuple[list[Event], int]:
        query = (select(Event).order_by(Event.event_time))
        count_query = select(func.count()).select_from(Event)

        if date_from is not None:
            query = query.where(Event.event_time >= date_from)
            count_query = count_query.where(Event.event_time >= date_from)

        query = query.offset((page - 1) * page_size).limit(page_size)

        total = await self._session.scalar(count_query)
        result = await self._session.execute(query)
        events = list(result.scalars().all())

        return events, total

    async def get(self, event_id: uuid.UUID) -> Event | None:
        return await self._session.get(Event, event_id)
