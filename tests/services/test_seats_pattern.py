from src.services.seats_pattern import is_valid_seat


def test_is_valid_seat_returns_true_for_seat_within_range():
    assert is_valid_seat("A1-1000,B1-2000", "A15") is True


def test_is_valid_seat_returns_false_for_unknown_section():
    assert is_valid_seat("A1-1000,B1-2000", "C15") is False


def test_is_valid_seat_returns_false_when_number_out_of_range():
    assert is_valid_seat("A1-1000", "A1500") is False
