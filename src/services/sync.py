from datetime import datetime, timezone

from ..database import async_session_factory
from ..models.event import Event
from ..repositories.event import EventRepository
from ..repositories.sync_meta import SyncMetaRepository
from .events_paginator import EventsPaginator
from .events_provider_client import EventsProviderClient
from .events_provider_schemas import ProviderEvent


def _parse_event(raw: dict) -> Event:
    provider_event = ProviderEvent.model_validate(raw)
    return Event(**provider_event.to_event_kwargs())


async def sync_events(client: EventsProviderClient):
    async with async_session_factory() as session:
        sync_meta_repo = SyncMetaRepository(session)
        event_repo = EventRepository(session)

        meta = await sync_meta_repo.get()
        changed_at_param = meta.last_changed_at.date().isoformat()
        latest_changed_at = meta.last_changed_at

        async for raw in EventsPaginator(client, changed_at=changed_at_param):
            await event_repo.upsert(_parse_event(raw))

            raw_changed_at = datetime.fromisoformat(raw["changed_at"])
            if raw_changed_at > latest_changed_at:
                latest_changed_at = raw_changed_at

        await sync_meta_repo.update(
            last_changed_at=latest_changed_at,
            last_sync_time=datetime.now(timezone.utc),
            sync_status="ok",
        )

        await session.commit()
