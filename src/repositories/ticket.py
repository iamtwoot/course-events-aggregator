import asyncio
import uuid

from sqlalchemy import delete
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ticket import Ticket

_MAX_ATTEMPTS = 3
_RETRY_DELAY_SECONDS = 0.5


class TicketRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_ticket_id(self, ticket_id: uuid.UUID) -> Ticket | None:
        return await self._session.get(Ticket, ticket_id)

    async def create(self, ticket_id: uuid.UUID, event_id: uuid.UUID) -> None:
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                self._session.add(Ticket(event_id=event_id, ticket_id=ticket_id))
                await self._session.commit()
                break
            except DBAPIError:
                await self._session.rollback()
                if attempt == _MAX_ATTEMPTS:
                    raise
                await asyncio.sleep(_RETRY_DELAY_SECONDS * attempt)

    async def delete_by_ticket_id(self, ticket_id: uuid.UUID) -> None:
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                await self._session.execute(
                    delete(Ticket).where(Ticket.ticket_id == ticket_id)
                )
                await self._session.commit()
                return
            except DBAPIError:
                await self._session.rollback()
                if attempt == _MAX_ATTEMPTS:
                    raise
                await asyncio.sleep(_RETRY_DELAY_SECONDS * attempt)
