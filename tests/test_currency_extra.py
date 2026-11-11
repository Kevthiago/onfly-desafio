"""Testes adicionais: câmbio para BRL (D4)."""

from decimal import Decimal

from helpers import run_cli

from onfly_report.services.currency_converter import convert_to_brl

RATES = {"BRL": Decimal("1.000000"), "USD": Decimal("5.420000"), "EUR": Decimal("5.880000")}


def test_convert_multiplies_amount_by_rate():
    assert convert_to_brl(Decimal("100.00"), "USD", RATES) == Decimal("542.00")
    assert convert_to_brl(Decimal("100.00"), "EUR", RATES) == Decimal("588.00")


def test_convert_brl_with_rate_one_keeps_amount():
    result = convert_to_brl(Decimal("123.45"), "BRL", RATES)
    assert result == Decimal("123.45")


def test_convert_is_exact_decimal_without_float_residue():
    """O produto exato em Decimal; float produziria resíduo (ex.: 108.34580000000001)."""
    result = convert_to_brl(Decimal("19.99"), "USD", RATES)
    assert isinstance(result, Decimal)
    assert result == Decimal("108.3458")
    assert convert_to_brl(Decimal("0.10"), "X", {"X": Decimal("3")}) == Decimal("0.30")
    assert convert_to_brl(Decimal("0.10"), "X", {"X": Decimal("1.1")}) == Decimal("0.110")


def test_eur_and_usd_in_report(tmp_path):
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "currency": "EUR", "amount": "100.00"},
            {"reservation_id": "R-2", "currency": "USD", "amount": "100.00", "hotel_id": "H02"},
        ],
    )
    assert report["summary"]["total_amount_brl"] == "1130.00"
    assert {h["hotel_id"]: h["total_brl"] for h in report["top_hotels"]} == {"H01": "588.00", "H02": "542.00"}


def test_brl_amount_is_not_changed(tmp_path):
    report = run_cli(tmp_path, [{"currency": "BRL", "amount": "1234.50"}])
    assert report["summary"]["total_amount_brl"] == "1234.50"


def test_rounding_only_at_serialization(tmp_path):
    """Duas reservas de 0.004 somam 0.008 e saem 0.01; arredondar por reserva daria 0.00."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "amount": "0.004"},
            {"reservation_id": "R-2", "amount": "0.004"},
        ],
    )
    assert report["summary"]["total_amount_brl"] == "0.01"
    assert report["by_month"][0]["total_brl"] == "0.01"
    assert report["top_hotels"][0]["total_brl"] == "0.01"
