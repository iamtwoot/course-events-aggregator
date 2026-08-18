from datetime import datetime
import uuid

from pydantic import BaseModel, Field


class PlaceOut(BaseModel):
    id: uuid.UUID = Field(..., description="Unique place UUID")
    name: str = Field(..., description="Place name")
    city: str = Field(..., description="Place city")
    address: str = Field(..., description="Place address")


class EventOut(BaseModel):
    id: uuid.UUID = Field(..., description="Unique event UUID")
    name: str = Field(..., description="Event name")
    place: PlaceOut = Field(..., description="Place")
    event_time: datetime = Field(..., description="Event time")
    registration_deadline: datetime = Field(..., description="Registration deadline")
    status: str = Field(..., description="Status")
    number_of_visitors: int = Field(..., description="Number of visitors")


class PaginatedEventsResponse(BaseModel):
    count: int = Field(..., description="Number of events")
    next: str | None = Field(..., description="Next page of events")
    previous: str | None = Field(..., description="Previous page of events")
    results: list[EventOut] = Field(..., description="Results")


class PlaceDetailOut(PlaceOut):
    seats_pattern: str | None = Field(default=None, description="Seats pattern")


class EventDetailOut(EventOut):
    place: PlaceDetailOut
