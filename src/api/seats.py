import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_events_provider_client
from src.database import get_db
from src.repositories.event import EventRepository
from src.schemas.seats import SeatsOut
from src.services.events_provider_client import EventsProviderClient

router = APIRouter()


@router.get("/api/events/{event_id}/seats")
async def list_free_seats(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    client: EventsProviderClient = Depends(get_events_provider_client),
) -> SeatsOut:
    repo = EventRepository(session)
    event = await repo.get(event_id)

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.status != "published":
        raise HTTPException(status_code=400, detail="Event is not published")

    raw = await client.get_free_seats(event.id)

    return SeatsOut(event_id=event_id, available_seats=raw["seats"])
