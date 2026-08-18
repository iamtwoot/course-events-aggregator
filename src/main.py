import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from sqlalchemy import text

from .config import settings
from .database import engine
from .services.events_provider_client import EventsProviderClient
from .services.sync import sync_events
from .api.events import router as events_router


async def sync_loop(client: EventsProviderClient):
    while True:
        try:
            await sync_events(client)
        except Exception:
            # log exception
            pass
        await asyncio.sleep(24 * 60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    http_client = httpx.AsyncClient(
        base_url=settings.events_provider_base_url,
        headers={"x-api-key": settings.events_provider_api_key},
        follow_redirects=True,
    )
    app.state.events_provider_client = EventsProviderClient(http_client)

    sync_task = asyncio.create_task(sync_loop(app.state.events_provider_client))

    yield

    sync_task.cancel()
    await http_client.aclose()
    await engine.dispose()


app = FastAPI(title="Events Aggregator", lifespan=lifespan)
app.include_router(events_router)


@app.get("/api/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/sync/trigger")
async def trigger_sync(request: Request):
    await sync_events(request.app.state.events_provider_client)
    return {"ok": True}
