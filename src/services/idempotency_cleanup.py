import logging
from datetime import datetime, timedelta, timezone

from src.config import settings
from src.database import async_session_factory
from src.repositories.idempotency import IdempotencyRepository

logger = logging.getLogger(__name__)


async def cleanup_expired_idempotency_keys() -> None:
    threshold = datetime.now(timezone.utc) - timedelta(
        days=settings.idempotency_key_ttl_days
    )
    async with async_session_factory() as session:
        deleted = await IdempotencyRepository(session).delete_expired(threshold)
        await session.commit()

    if deleted:
        logger.info("Deleted %s expired idempotency keys", deleted)
