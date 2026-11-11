"""Testes adicionais: moeda sem taxa de câmbio é entrada inválida (exit 2)."""

import csv
import json
import os
import subprocess
import sys

from helpers import BASE, COLUMNS, PROJECT_ROOT, SRC_DIR

RATES = "currency,rate_to_brl\nBRL,1.000000\nUSD,5.420000\nEUR,5.880000\n"


def _run(tmp_path, rows):
    input_path = tmp_path / "reservas.csv"
    rates_path = tmp_path / "rates.csv"
    output_path = tmp_path / "report.json"
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({**BASE, **row} for row in rows)
    rates_path.write_text(RATES, encoding="utf-8")

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + environment.get("PYTHONPATH", "")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.run(
        [
            sys.executable, "-m", "onfly_report",
            "--input", str(input_path),
            "--rates", str(rates_path),
            "--output", str(output_path),
        ],
        cwd=str(PROJECT_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    return process, output_path


def test_currency_without_rate_exits_with_2_and_names_the_currency(tmp_path):
    process, output_path = _run(
        tmp_path,
        [
            {"reservation_id": "R-1", "currency": "BRL"},
            {"reservation_id": "R-2", "currency": "GBP", "amount": "80.00"},
        ],
    )
    assert process.returncode == 2
    assert "GBP" in process.stderr
    assert "sem taxa de câmbio" in process.stderr
    assert "Traceback" not in process.stderr
    assert not output_path.exists()


def test_currency_with_rate_still_succeeds(tmp_path):
    process, output_path = _run(
        tmp_path,
        [
            {"reservation_id": "R-1", "currency": "USD", "amount": "100.00"},
            {"reservation_id": "R-2", "currency": "EUR", "amount": "100.00"},
        ],
    )
    assert process.returncode == 0, process.stderr
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["summary"]["total_amount_brl"] == "1130.00"
