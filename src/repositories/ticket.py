import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ticket import Ticket


class TicketRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, ticket_id: uuid.UUID, event_id: uuid.UUID):
        self._session.add(Ticket(event_id=event_id, ticket_id=ticket_id))
