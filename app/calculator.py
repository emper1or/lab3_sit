"""Расчёт аннуитетного ипотечного платежа.

Модуль не зависит от FastAPI и может использоваться отдельно (CLI, тесты,
другие сервисы). Все денежные величины возвращаются как float.
"""

from __future__ import annotations
import os
from typing import Dict

# Количество платежей в году (стандартная аннуитетная схема — 12 платежей).
PAYMENTS_PER_YEAR = 12


def _annuity_payment(principal: float, monthly_rate: float, months: int) -> float:
    """Величина аннуитетного платежа.

    Формула: P = S * i / (1 - (1 + i) ** -n),
    где S — сумма кредита, i — месячная ставка, n — число месяцев.
    При i == 0 формула вырождается в S / n (беспроцентный кредит).
    """
    if monthly_rate == 0:
        return principal / months

    factor = monthly_rate / (1 - (1 + monthly_rate) ** (-months))
    return principal * factor


def calculate_mortgage(amount: float, annual_rate: float, years: int) -> Dict[str, float]:
    """Рассчитать параметры аннуитетной ипотеки.

    :param amount: сумма кредита в рублях (> 0).
    :param annual_rate: годовая процентная ставка в процентах (>= 0).
    :param years: срок кредита в годах (> 0, целое).
    :return: словарь с месячным платежом, итоговой суммой и переплатой.
    :raises ValueError: если любой из аргументов неположителен
        (ставка может быть равна нулю, но не отрицательна).
    """
    if amount <= 0:
        raise ValueError("Сумма кредита должна быть положительной")
    if annual_rate < 0:
        raise ValueError("Годовая ставка не может быть отрицательной")
    if years <= 0:
        raise ValueError("Срок кредита должен быть положительным")

    months = int(years) * PAYMENTS_PER_YEAR
    monthly_rate = annual_rate / 100 / PAYMENTS_PER_YEAR

    monthly_payment = _annuity_payment(amount, monthly_rate, months)
    total_payment = monthly_payment * months
    overpayment = total_payment - amount

    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "overpayment": round(overpayment, 2),
        "months": months,
    }
