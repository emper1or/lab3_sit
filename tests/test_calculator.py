"""Тесты расчёта ипотеки и веб-интерфейса."""

import pytest
from fastapi.testclient import TestClient

from app.calculator import calculate_mortgage
from app.main import app

client = TestClient(app)


def test_standard_mortgage():
    """Проверка математики: 1 000 000 ₽ под 12% годовых на 1 год."""
    result = calculate_mortgage(1_000_000, 12, 1)

    # i = 0.12 / 12 = 0.01, n = 12
    # P = 1e6 * 0.01 / (1 - 1.01^-12) = 88 848.788...
    assert result["monthly_payment"] == pytest.approx(88_848.79, abs=0.01)
    assert result["months"] == 12

    # Итоговая сумма и переплата согласованы с платежом.
    assert result["total_payment"] == pytest.approx(1_066_185.48, abs=0.05)
    assert result["overpayment"] == pytest.approx(66_185.48, abs=0.05)
    assert result["total_payment"] == pytest.approx(result["monthly_payment"] * 12, abs=0.1)
    assert result["overpayment"] == pytest.approx(
        result["total_payment"] - 1_000_000, abs=0.05
    )


def test_standard_mortgage_long_term():
    """Длинный срок: 3 000 000 ₽ под 10% на 20 лет."""
    result = calculate_mortgage(3_000_000, 10, 20)

    assert result["months"] == 240
    assert result["monthly_payment"] == pytest.approx(28_950.65, abs=0.01)
    assert result["total_payment"] > 3_000_000
    assert result["overpayment"] > 0


def test_zero_rate():
    """Ставка 0%: платёж равен сумме кредита, делённой на число месяцев."""
    result = calculate_mortgage(1_200_000, 0, 1)

    assert result["monthly_payment"] == pytest.approx(100_000.0, abs=0.01)
    assert result["total_payment"] == pytest.approx(1_200_000.0, abs=0.01)
    assert result["overpayment"] == pytest.approx(0.0, abs=0.01)

    result_5y = calculate_mortgage(1_200_000, 0, 5)
    assert result_5y["monthly_payment"] == pytest.approx(30_000.0, abs=0.01)
    assert result_5y["overpayment"] == pytest.approx(0.0, abs=0.01)


@pytest.mark.parametrize(
    ("amount", "annual_rate", "years"),
    [
        (-1_000_000, 12, 10),
        (0, 12, 10),
        (1_000_000, -5, 10),
        (1_000_000, 12, 0),
        (1_000_000, 12, -3),
        (-1, -1, -1),
    ],
)
def test_invalid_values(amount, annual_rate, years):
    """Некорректные параметры должны приводить к ValueError."""
    with pytest.raises(ValueError):
        calculate_mortgage(amount, annual_rate, years)


def test_api_homepage():
    """GET / возвращает 200 и HTML-форму с тремя полями ввода."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert 'name="amount"' in body
    assert 'name="annual_rate"' in body
    assert 'name="years"' in body
    assert 'method="post"' in body


def test_api_calculate():
    """POST / принимает форму и отдаёт страницу с результатами."""
    response = client.post(
        "/",
        data={"amount": "1000000", "annual_rate": "12", "years": "1"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "88 848,79" in response.text or "88 848.79" in response.text
    assert "Переплата" in response.text


def test_api_calculate_invalid_values():
    """POST / с отрицательной суммой возвращает страницу с сообщением об ошибке."""
    response = client.post(
        "/",
        data={"amount": "-1000", "annual_rate": "12", "years": "1"},
    )

    assert response.status_code == 400
    assert "Сумма кредита должна быть положительной" in response.text
