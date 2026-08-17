from datetime import datetime
from uuid import UUID

import pydantic


class ProviderPlace(pydantic.BaseModel):
    id: UUID
    name: str
    city: str
    address: str
    seats_pattern: str | None


class ProviderEvent(pydantic.BaseModel):
    id: UUID
    name: str
    place: ProviderPlace
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int
    changed_at: datetime

    def to_event_kwargs(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "place_id": self.place.id,
            "place_name": self.place.name,
            "place_city": self.place.city,
            "place_address": self.place.address,
            "place_seats_pattern": self.place.seats_pattern,
            "event_time": self.event_time,
            "registration_deadline": self.registration_deadline,
            "status": self.status,
            "number_of_visitors": self.number_of_visitors,
        }
