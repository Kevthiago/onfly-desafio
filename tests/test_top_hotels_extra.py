"""Testes adicionais: ranking de hotéis (D5)."""

from helpers import run_cli


def _row(reservation_id: str, hotel_id: str, amount: str) -> dict[str, str]:
    return {
        "reservation_id": reservation_id,
        "hotel_id": hotel_id,
        "hotel_name": f"Hotel {hotel_id}",
        "amount": amount,
    }


def _ids(report: dict) -> list[str]:
    return [hotel["hotel_id"] for hotel in report["top_hotels"]]


def test_tie_is_broken_by_hotel_id_ascending(tmp_path):
    """Empate de total_brl: hotel_id crescente decide, mesmo com a ordem inversa no arquivo."""
    report = run_cli(
        tmp_path,
        [
            _row("R-1", "H03", "500.00"),
            _row("R-2", "H02", "1000.00"),
            _row("R-3", "H01", "1000.00"),
        ],
    )
    assert _ids(report) == ["H01", "H02", "H03"]
    assert [hotel["total_brl"] for hotel in report["top_hotels"]] == ["1000.00", "1000.00", "500.00"]


def test_tie_among_lowest_totals_still_ascending_by_id(tmp_path):
    report = run_cli(
        tmp_path,
        [
            _row("R-1", "H09", "300.00"),
            _row("R-2", "H05", "300.00"),
            _row("R-3", "H07", "900.00"),
        ],
    )
    assert _ids(report) == ["H07", "H05", "H09"]


def test_top_one_returns_only_the_highest(tmp_path):
    report = run_cli(
        tmp_path,
        [_row("R-1", "H01", "100.00"), _row("R-2", "H02", "300.00"), _row("R-3", "H03", "200.00")],
        top=1,
    )
    assert _ids(report) == ["H02"]


def test_top_greater_than_number_of_hotels_returns_existing_ones(tmp_path):
    report = run_cli(
        tmp_path,
        [_row("R-1", "H01", "100.00"), _row("R-2", "H02", "300.00"), _row("R-3", "H03", "200.00")],
        top=10,
    )
    assert _ids(report) == ["H02", "H03", "H01"]


def test_ordering_is_numeric_not_textual(tmp_path):
    """'900.00' > '1000.00' como texto; o ranking deve comparar valores."""
    report = run_cli(
        tmp_path,
        [_row("R-1", "H01", "900.00"), _row("R-2", "H02", "1000.00"), _row("R-3", "H03", "95.50")],
    )
    assert _ids(report) == ["H02", "H01", "H03"]
    assert [hotel["total_brl"] for hotel in report["top_hotels"]] == ["1000.00", "900.00", "95.50"]


def test_hotel_totals_are_summed_across_reservations(tmp_path):
    report = run_cli(
        tmp_path,
        [_row("R-1", "H01", "400.00"), _row("R-2", "H01", "400.00"), _row("R-3", "H02", "700.00")],
    )
    assert _ids(report) == ["H01", "H02"]
    assert report["top_hotels"][0]["total_brl"] == "800.00"
    assert report["top_hotels"][0]["room_nights"] == 2
