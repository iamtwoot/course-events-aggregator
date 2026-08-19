import uuid

from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid)

    def __repr__(self) -> str:
        return f"<Ticket (id={self.ticket_id}, event_id={self.event_id})>"
