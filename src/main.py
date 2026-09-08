import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

import httpx
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.services.notifications_client import NotificationsClient
from src.services.outbox_worker import process_outbox_batch

from .api.events import router as events_router
from .api.seats import router as seats_router
from .api.tickets import router as tickets_router
from .config import settings
from .database import engine
from .services.events_provider_client import EventsProviderClient
from .services.sync import sync_events

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        send_default_pii=False,
    )


async def sync_loop(client: EventsProviderClient):
    while True:
        try:
            await sync_events(client)
        except Exception:
            logger.exception("Background sync failed")
        await asyncio.sleep(24 * 60 * 60)


async def outbox_loop(client: NotificationsClient):
    while True:
        try:
            await process_outbox_batch(client)
        except Exception:
            logger.exception("Outbox worker iteration failed")
        await asyncio.sleep(settings.outbox_poll_interval_seconds)


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

    notifications_http_client = httpx.AsyncClient(
        base_url=settings.capashino_base_url,
        headers={"X-API-Key": settings.capashino_api_key},
    )
    notifications_client = NotificationsClient(notifications_http_client)

    sync_task = asyncio.create_task(sync_loop(app.state.events_provider_client))
    outbox_task = asyncio.create_task(outbox_loop(notifications_client))

    yield

    sync_task.cancel()
    outbox_task.cancel()
    for task in (sync_task, outbox_task):
        with contextlib.suppress(asyncio.CancelledError):
            await task

    await http_client.aclose()
    await notifications_http_client.aclose()
    await engine.dispose()


app = FastAPI(title="Events Aggregator", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": jsonable_encoder(exc.errors())},
    )


app.include_router(events_router)
app.include_router(seats_router)
app.include_router(tickets_router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/sync/trigger")
async def trigger_sync(request: Request):
    await sync_events(request.app.state.events_provider_client)
    return {"status": "ok"}


@app.get("/api/debug/sentry")
async def trigger_error():
    raise RuntimeError("GlitchTip integration check")
