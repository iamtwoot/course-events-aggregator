import logging

import httpx

from src.config import settings
from src.database import async_session_factory
from src.models.outbox import OutboxRecord, OutboxStatus
from src.repositories.outbox import OutboxRepository
from src.services.notifications_client import NotificationsClient

_TICKET_PURCHASE_MESSAGE = "Вы успешно зарегистрированы на мероприятие - {event_name}"

logger = logging.getLogger(__name__)


async def _deliver(client: NotificationsClient, record: OutboxRecord) -> None:
    await client.create_notification(
        message=_TICKET_PURCHASE_MESSAGE.format(
            event_name=record.payload["event_name"]
        ),
        reference_id=record.payload["ticket_id"],
        idempotency_key=str(record.id),
    )


async def process_outbox_batch(client: NotificationsClient) -> None:
    async with async_session_factory() as session:
        repo = OutboxRepository(session)
        records = await repo.list_pending(limit=settings.outbox_batch_size)

        for record in records:
            try:
                await _deliver(client, record)
            except httpx.HTTPError:
                repo.mark_failed(record, settings.outbox_max_attempts)
                if record.status == OutboxStatus.FAILED:
                    logger.error(
                        "Outbox record gave up after %s attempts: %s",
                        record.attempts,
                        record.id,
                    )
                else:
                    logger.warning("Outbox delivery failed, will retry: %s", record.id)
            else:
                logger.info("Outbox record delivered: %s", record.id)
                repo.mark_sent(record)
            await session.commit()
