"""Conversão de valores para BRL."""

from __future__ import annotations

from decimal import Decimal

from ..exceptions import InputFileError


def convert_to_brl(amount: Decimal, currency: str, rates: dict[str, Decimal]) -> Decimal:
    """Converte um valor na moeda informada para BRL usando a taxa da tabela.

    Moeda ausente da tabela de câmbio é entrada inválida (InputFileError, exit 2 no CLI).
    """
    try:
        rate = rates[currency]
    except KeyError:
        raise InputFileError(f"moeda {currency} sem taxa de câmbio") from None
    return amount * rate
