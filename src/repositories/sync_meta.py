from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.event import SyncMeta


class SyncMetaRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self) -> SyncMeta:
        meta = await self._session.get(SyncMeta, 1)
        if meta is None:
            meta = SyncMeta(id=1)
            self._session.add(meta)
            await self._session.flush()
        return meta

    async def update(
        self,
        *,
        last_changed_at: datetime,
        last_sync_time: datetime,
        sync_status: str,
    ) -> None:
        meta = await self.get()
        meta.last_changed_at = last_changed_at
        meta.last_sync_time = last_sync_time
        meta.sync_status = sync_status
