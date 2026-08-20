import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_events_provider_client
from src.database import get_db
from src.repositories.event import EventRepository
from src.repositories.ticket import TicketRepository
from src.schemas.ticket import TicketCancelOut, TicketOut, TicketRegistration
from src.services.events_provider_client import EventsProviderClient
from src.services.seats_cache import seats_cache
from src.services.ticket_usecases import (
    CancelTicketUsecase,
    CreateTicketUsecase,
    EventNotAvailableError,
    EventNotFoundError,
    InvalidSeatError,
    ProviderTemporarilyUnavailableError,
    SeatTakenError,
    TicketNotFoundError,
)

router = APIRouter()


@router.post("/api/tickets", status_code=201, response_model=TicketOut)
async def register_ticket(
    payload: TicketRegistration,
    session: AsyncSession = Depends(get_db),
    client: EventsProviderClient = Depends(get_events_provider_client),
):
    usecase = CreateTicketUsecase(
        client=client,
        events=EventRepository(session),
        tickets=TicketRepository(session),
        seats_cache=seats_cache,
    )

    try:
        ticket_id = await usecase.do(payload)
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotAvailableError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidSeatError:
        raise HTTPException(
            status_code=400, detail="Seat does not exist for this venue"
        )
    except SeatTakenError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ProviderTemporarilyUnavailableError:
        raise HTTPException(
            status_code=409,
            detail="Event status changed since last sync, try again later",
        )

    return TicketOut(ticket_id=ticket_id)


@router.delete("/api/tickets/{ticket_id}")
async def unregister_ticket(
    ticket_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    client: EventsProviderClient = Depends(get_events_provider_client),
):
    usecase = CancelTicketUsecase(
        client=client,
        tickets=TicketRepository(session),
        seats_cache=seats_cache,
    )

    try:
        await usecase.do(ticket_id)
    except TicketNotFoundError:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return TicketCancelOut(success=True)
