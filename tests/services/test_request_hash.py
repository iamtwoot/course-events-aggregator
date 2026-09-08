import uuid

from src.schemas.ticket import TicketRegistration
from src.services.ticket_usecases import _request_hash


def _payload(**overrides) -> TicketRegistration:
    defaults = dict(
        event_id=uuid.uuid4(),
        first_name="Ivan",
        last_name="Ivanov",
        email="example@example.com",
        seat="A15",
    )
    defaults.update(overrides)
    return TicketRegistration(**defaults)


def test_same_data_gives_same_hash():
    event_id = uuid.uuid4()
    assert _request_hash(_payload(event_id=event_id)) == _request_hash(
        _payload(event_id=event_id)
    )


def test_different_seat_gives_different_hash():
    event_id = uuid.uuid4()
    assert _request_hash(_payload(event_id=event_id, seat="A15")) != _request_hash(
        _payload(event_id=event_id, seat="A16")
    )


def test_idempotency_key_does_not_affect_hash():
    event_id = uuid.uuid4()
    assert _request_hash(
        _payload(event_id=event_id, idempotency_key="K1")
    ) == _request_hash(_payload(event_id=event_id, idempotency_key="K2"))


def test_hash_is_sha256_hex():
    assert len(_request_hash(_payload())) == 64
