from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.event import Event
from src.repositories.event import EventRepository
from src.schemas.event import EventOut, PaginatedEventsResponse, PlaceOut

router = APIRouter()


def _to_event_out(event: Event) -> EventOut:
    return EventOut(
        id=event.id,
        name=event.name,
        place=PlaceOut(
            id=event.place_id,
            name=event.place_name,
            city=event.place_city,
            address=event.place_address,
        ),
        event_time=event.event_time,
        registration_deadline=event.registration_deadline,
        status=event.status,
        number_of_visitors=event.number_of_visitors,
    )


@router.get("/api/events")
async def list_events(
        request: Request,
        session: AsyncSession = Depends(get_db),
        date_from: date | None = None,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedEventsResponse:
    repo = EventRepository(session)
    events, total = await repo.list(date_from=date_from, page=page, page_size=page_size)

    has_next = page * page_size < total
    next_url = str(request.url.include_query_params(page=page + 1)) if has_next else None
    previous_url = str(request.url.include_query_params(page=page - 1)) if page > 1 else None

    return PaginatedEventsResponse(
        count=total,
        next=next_url,
        previous=previous_url,
        results=[_to_event_out(event) for event in events],
    )
