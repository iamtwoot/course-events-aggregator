import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from .database import engine


async def sync_events():
    pass


async def sync_loop():
    while True:
        try:
            await sync_events()
        except Exception:
            # log exception
            pass
        await asyncio.sleep(24 * 60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    sync_task = asyncio.create_task(sync_loop())

    yield

    sync_task.cancel()
    await engine.dispose()


app = FastAPI(title="Events Aggregator", lifespan=lifespan)


@app.get("/api/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/sync/trigger")
async def trigger_sync():
    await sync_events()
    return {"ok": True}
