import asyncio
import uuid
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_events_provider_client
from src.database import get_db
from src.repositories.event import EventRepository
from src.repositories.ticket import TicketRepository
from src.schemas.ticket import TicketCancelOut, TicketOut, TicketRegistration
from src.services.events_provider_client import EventsProviderClient
from src.services.seats_cache import seats_cache
from src.services.seats_pattern import is_valid_seat
from src.timezone import MSK

router = APIRouter()

LOCAL_SAVE_MAX_ATTEMPTS = 3
LOCAL_SAVE_RETRY_DELAY_SECONDS = 0.5


@router.post("/api/tickets", status_code=201, response_model=TicketOut)
async def register_ticket(
    payload: TicketRegistration,
    session: AsyncSession = Depends(get_db),
    client: EventsProviderClient = Depends(get_events_provider_client),
):
    event_repo = EventRepository(session)
    event = await event_repo.get(payload.event_id)

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.status != "published":
        raise HTTPException(status_code=400, detail="Event is not published")

    if event.registration_deadline < datetime.now(MSK):
        raise HTTPException(status_code=400, detail="Registration is closed")

    if event.place_seats_pattern is None or not is_valid_seat(
        event.place_seats_pattern, payload.seat
    ):
        raise HTTPException(
            status_code=400, detail="Seat does not exist for this venue"
        )

    available_seats = seats_cache.get(str(event.id))
    if available_seats is None:
        try:
            raw = await client.get_free_seats(event.id)
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=409,
                detail="Event status changed since last sync, try again later",
            ) from e
        available_seats = raw["seats"]
        seats_cache.set(str(event.id), available_seats)

    if payload.seat not in available_seats:
        raise HTTPException(status_code=400, detail="Seat is already taken")

    try:
        ticket_id = await client.register(event.id, payload)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            try:
                body = e.response.json()
            except ValueError:
                provider_detail = e.response.text
            else:
                provider_detail = (
                    body.get("detail", body) if isinstance(body, dict) else body
                )
            raise HTTPException(status_code=400, detail=provider_detail) from e
        raise

    available_seats.remove(payload.seat)
    seats_cache.set(str(event.id), available_seats)

    # The provider already created the ticket at this point, so a failure to
    # save it locally must not be given up on immediately - retry a few times
    # before losing track of a ticket that exists on the provider's side.
    ticket_repo = TicketRepository(session)
    for attempt in range(1, LOCAL_SAVE_MAX_ATTEMPTS + 1):
        try:
            await ticket_repo.create(ticket_id=ticket_id, event_id=payload.event_id)
            await session.commit()
            break
        except DBAPIError:
            await session.rollback()
            if attempt == LOCAL_SAVE_MAX_ATTEMPTS:
                raise
            await asyncio.sleep(LOCAL_SAVE_RETRY_DELAY_SECONDS * attempt)

    return TicketOut(ticket_id=ticket_id)


@router.delete("/api/tickets/{ticket_id}")
async def unregister_ticket(
    ticket_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    client: EventsProviderClient = Depends(get_events_provider_client),
):
    ticket_repo = TicketRepository(session)
    ticket = await ticket_repo.get_by_ticket_id(ticket_id)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    event_id = ticket.event_id

    try:
        await client.unregister(event_id, ticket_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Registration not found") from e
        raise

    # The provider has already cancelled the registration at this point, so a
    # failure to delete it locally must not be given up on immediately - retry
    # a few times before losing sync with the provider's state.
    for attempt in range(1, LOCAL_SAVE_MAX_ATTEMPTS + 1):
        try:
            await ticket_repo.delete_by_ticket_id(ticket_id)
            await session.commit()
            break
        except DBAPIError:
            await session.rollback()
            if attempt == LOCAL_SAVE_MAX_ATTEMPTS:
                raise
            await asyncio.sleep(LOCAL_SAVE_RETRY_DELAY_SECONDS * attempt)

    seats_cache.invalidate(str(event_id))

    return TicketCancelOut(success=True)
