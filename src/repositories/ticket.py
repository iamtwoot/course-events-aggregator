import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.enums import TicketStatus
from src.models.ticket import Ticket


class TicketRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_ticket_id(self, ticket_id: uuid.UUID) -> Ticket | None:
        return await self._session.get(Ticket, ticket_id)

    def add(self, ticket_id: uuid.UUID, event_id: uuid.UUID) -> None:
        self._session.add(Ticket(event_id=event_id, ticket_id=ticket_id))

    async def set_cancelled(self, ticket_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Ticket)
            .where(Ticket.ticket_id == ticket_id)
            .values(status=TicketStatus.CANCELLED)
        )

    async def count(self) -> int:
        return await self._session.scalar(select(func.count()).select_from(Ticket)) or 0

    async def count_cancelled(self) -> int:
        return (
            await self._session.scalar(
                select(func.count())
                .select_from(Ticket)
                .where(Ticket.status == TicketStatus.CANCELLED)
            )
            or 0
        )
