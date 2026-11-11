"""Testes adicionais: noites de quarto (D3)."""

from datetime import date

import pytest
from helpers import run_cli

from onfly_report.services.stay_calculator import calculate_room_nights


@pytest.mark.parametrize(
    ("checkin", "checkout", "rooms", "expected"),
    [
        (date(2025, 1, 10), date(2025, 1, 13), 1, 3),  # mesmo mês, sem virada
        (date(2025, 1, 30), date(2025, 2, 2), 1, 3),  # virada de mês
        (date(2024, 12, 30), date(2025, 1, 2), 1, 3),  # virada de ano
        (date(2024, 12, 30), date(2025, 1, 2), 2, 6),  # virada de ano com 2 quartos
        (date(2025, 2, 27), date(2025, 3, 2), 1, 3),  # fevereiro (28 dias)
        (date(2025, 1, 10), date(2025, 1, 11), 3, 3),  # 1 noite, 3 quartos
    ],
)
def test_calculate_room_nights(checkin, checkout, rooms, expected):
    assert calculate_room_nights(checkin, checkout, rooms) == expected


def test_rooms_multiply_nights_but_not_amount(tmp_path):
    """Vários quartos multiplicam as noites, e o valor da reserva permanece o informado."""
    report = run_cli(
        tmp_path,
        [
            {
                "checkin_date": "2024-12-30",
                "checkout_date": "2025-01-02",
                "rooms": "2",
                "amount": "300.00",
            }
        ],
    )
    assert report["summary"]["total_room_nights"] == 6
    assert report["summary"]["total_amount_brl"] == "300.00"
    assert report["summary"]["average_nightly_rate_brl"] == "50.00"
    assert report["by_month"] == [
        {"month": "2024-12", "reservations": 1, "room_nights": 6, "total_brl": "300.00"}
    ]
