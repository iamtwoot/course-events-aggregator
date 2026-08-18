import uuid

from pydantic import BaseModel, Field


class SeatsOut(BaseModel):
    event_id: uuid.UUID = Field(..., description="Event UUID")
    available_seats: list[str] = Field(..., description="Available seats")
