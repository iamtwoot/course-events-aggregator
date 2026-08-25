import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.seats_usecases import GetFreeSeatsUsecase
from src.services.ticket_usecases import (
    EventNotAvailableError,
    EventNotFoundError,
    ProviderTemporarilyUnavailableError,
)
from src.api.dependencies import get_events_provider_client
from src.database import get_db
from src.repositories.event import EventRepository
from src.schemas.seats import SeatsOut
from src.services.events_provider_client import EventsProviderClient
from src.services.seats_cache import seats_cache

router = APIRouter()


@router.get("/api/events/{event_id}/seats")
async def list_free_seats(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    client: EventsProviderClient = Depends(get_events_provider_client),
) -> SeatsOut:
    usecase = GetFreeSeatsUsecase(
        client=client,
        events=EventRepository(session),
        seats_cache=seats_cache,
    )

    try:
        seats = await usecase.do(event_id)
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotAvailableError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ProviderTemporarilyUnavailableError:
        raise HTTPException(
            status_code=409,
            detail="Event status changed since last sync, try again later",
        )
    return SeatsOut(event_id=event_id, available_seats=seats)
