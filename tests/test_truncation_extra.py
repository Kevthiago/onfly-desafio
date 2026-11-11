"""Testes adicionais: nenhuma reserva do arquivo pode ser descartada (D1)."""

import pytest
from helpers import run_cli


def _rows(count: int) -> list[dict[str, str]]:
    return [{"reservation_id": f"R-{index:04d}", "amount": "1.00"} for index in range(1, count + 1)]


@pytest.mark.parametrize("count", [199, 200, 201, 250, 300])
def test_all_rows_are_read(tmp_path, count):
    report = run_cli(tmp_path, _rows(count))
    summary = report["summary"]
    assert summary["total_reservations"] == count
    assert summary["confirmed_reservations"] == count
    assert summary["total_room_nights"] == count
    assert summary["total_amount_brl"] == f"{count}.00"


def test_rows_after_the_200th_enter_the_aggregates(tmp_path):
    """A última linha do arquivo (posição 250) precisa aparecer no ranking e no by_month."""
    rows = _rows(249)
    rows.append(
        {
            "reservation_id": "R-LAST",
            "hotel_id": "H99",
            "hotel_name": "Hotel Final",
            "checkin_date": "2025-03-10",
            "checkout_date": "2025-03-12",
            "amount": "5000.00",
        }
    )
    report = run_cli(tmp_path, rows)
    assert report["summary"]["total_reservations"] == 250
    assert report["top_hotels"][0]["hotel_id"] == "H99"
    assert {item["month"] for item in report["by_month"]} == {"2025-01", "2025-03"}
