from datetime import date
from src.utils.helpers import get_beginning_next_month
from src.utils import constants


def test_get_beginning_next_month_regular_case():
    current_date = date(2023, 11, 3)
    result = get_beginning_next_month(current_date)
    expected = date(2023, constants.DECEMBER, 1)

    assert result == expected


def test_get_beginning_next_month_december_case():
    current_date = date(2023, 12, 18)
    result = get_beginning_next_month(current_date)
    expected = date(2024, 1, 1)

    assert result == expected


def test_get_beginning_next_month_end_of_month():
    current_date = date(2024, 4, 30)
    result = get_beginning_next_month(current_date)
    expected = date(2024, 5, 1)

    assert result == expected
