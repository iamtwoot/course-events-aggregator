import uuid

from pydantic import BaseModel, EmailStr, Field


class TicketRegistration(BaseModel):
    event_id: uuid.UUID = Field(..., description="Event UUID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: EmailStr = Field(..., description="Email")
    seat: str = Field(..., description="Seat number")
    idempotency_key: str | None = Field(default=None, max_length=255)


class TicketOut(BaseModel):
    ticket_id: uuid.UUID = Field(..., description="Ticket UUID")


class TicketCancelOut(BaseModel):
    success: bool = Field(..., description="Success")
