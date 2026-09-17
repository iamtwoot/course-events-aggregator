import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.enums import TicketStatus


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    status: Mapped[TicketStatus] = mapped_column(
        SAEnum(
            TicketStatus,
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        default=TicketStatus.ACTIVE,
        server_default=TicketStatus.ACTIVE.value,
    )

    def __repr__(self) -> str:
        return f"<Ticket (id={self.ticket_id}, event_id={self.event_id})>"
