"""Testes adicionais: regras de status (D2)."""

import pytest
from helpers import run_cli

from onfly_report.services.status_policy import is_billable


@pytest.mark.parametrize(
    ("status", "expected"),
    [("CONFIRMED", True), ("CANCELLED", False), ("NO_SHOW", False), ("PENDING", False)],
)
def test_only_confirmed_is_billable(status, expected):
    assert is_billable(status) is expected


def test_cancelled_and_no_show_only_count_in_status_totals(tmp_path):
    """CANCELLED e NO_SHOW contam nas reservas, mas não em noites, valor, by_month nem top_hotels."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H01", "amount": "100.00"},
            {
                "reservation_id": "R-2",
                "status": "CANCELLED",
                "hotel_id": "H02",
                "hotel_name": "Hotel Cancelado",
                "checkin_date": "2025-03-10",
                "checkout_date": "2025-03-14",
                "rooms": "2",
                "amount": "500.00",
            },
            {
                "reservation_id": "R-3",
                "status": "NO_SHOW",
                "hotel_id": "H03",
                "hotel_name": "Hotel No Show",
                "checkin_date": "2025-04-10",
                "checkout_date": "2025-04-12",
                "amount": "300.00",
            },
        ],
    )
    summary = report["summary"]
    assert summary["total_reservations"] == 3
    assert summary["confirmed_reservations"] == 1
    assert summary["cancelled_reservations"] == 1
    assert summary["no_show_reservations"] == 1
    assert summary["total_room_nights"] == 1
    assert summary["total_amount_brl"] == "100.00"
    assert summary["average_nightly_rate_brl"] == "100.00"
    assert report["by_month"] == [
        {"month": "2025-01", "reservations": 1, "room_nights": 1, "total_brl": "100.00"}
    ]
    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H01"]


def test_unknown_status_is_not_billable(tmp_path):
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "amount": "100.00"},
            {"reservation_id": "R-2", "status": "PENDING", "hotel_id": "H02", "amount": "70.00"},
        ],
    )
    summary = report["summary"]
    assert summary["total_reservations"] == 2
    assert summary["confirmed_reservations"] == 1
    assert summary["total_room_nights"] == 1
    assert summary["total_amount_brl"] == "100.00"
    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H01"]


def test_period_without_billable_nights(tmp_path):
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "status": "CANCELLED", "amount": "100.00"},
            {"reservation_id": "R-2", "status": "CANCELLED", "amount": "200.00"},
        ],
    )
    assert report["summary"] == {
        "total_reservations": 2,
        "confirmed_reservations": 0,
        "cancelled_reservations": 2,
        "no_show_reservations": 0,
        "total_room_nights": 0,
        "total_amount_brl": "0.00",
        "average_nightly_rate_brl": "0.00",
    }
    assert report["by_month"] == []
    assert report["top_hotels"] == []
