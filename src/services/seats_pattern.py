import re

_SEAT_RE = re.compile(r"^([A-Z]+)(\d+)$")
_RANGE_RE = re.compile(r"^([A-Z]+)(\d+)-(\d+)$")


def is_valid_seat(seats_pattern: str, seat: str) -> bool:
    seat_match = _SEAT_RE.match(seat)
    if not seat_match:
        return False

    seat_section, seat_number = seat_match.group(1), int(seat_match.group(2))

    for chunk in seats_pattern.split(","):
        range_match = _RANGE_RE.match(chunk.strip())
        if not range_match:
            continue

        section, start, end = (
            range_match.group(1),
            int(range_match.group(2)),
            int(range_match.group(3)),
        )
        if section == seat_section and start <= seat_number <= end:
            return True

    return False
