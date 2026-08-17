import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.timezone import MSK


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    place_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    place_name: Mapped[str] = mapped_column(String)
    place_city: Mapped[str] = mapped_column(String)
    place_address: Mapped[str] = mapped_column(String)
    place_seats_pattern: Mapped[str | None] = mapped_column(String)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String)
    number_of_visitors: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"Event(id={self.id}, name={self.name})"


class SyncMeta(Base):
    __tablename__ = "sync_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    last_sync_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime(2000, 1, 1, tzinfo=MSK)
    )
    sync_status: Mapped[str] = mapped_column(String, default="never_run")
