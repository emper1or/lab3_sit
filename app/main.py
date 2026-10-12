"""FastAPI-приложение: онлайн-калькулятор ипотеки.

Запуск для разработки:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from html import escape

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from app.calculator import calculate_mortgage

app = FastAPI(
    title="Ипотечный калькулятор",
    description="Расчёт аннуитетного платежа по ипотеке",
    version="1.0.0",
)

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Ипотечный калькулятор</title>
    <style>
        :root {{
            --bg: #eef2f7;
            --card: #ffffff;
            --accent: #2563eb;
            --accent-dark: #1d4ed8;
            --text: #1f2937;
            --muted: #6b7280;
            --border: #d7dee8;
            --error-bg: #fef2f2;
            --error-text: #b91c1c;
            --error-border: #fecaca;
        }}

        * {{ box-sizing: border-box; }}

        body {{
            margin: 0;
            padding: 40px 16px;
            min-height: 100vh;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            background: var(--bg);
            color: var(--text);
            font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 16px;
            line-height: 1.5;
        }}

        .card {{
            width: 100%;
            max-width: 520px;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 32px;
            box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
        }}

        h1 {{
            margin: 0 0 4px;
            font-size: 24px;
            letter-spacing: -0.01em;
        }}

        .subtitle {{
            margin: 0 0 28px;
            color: var(--muted);
            font-size: 14px;
        }}

        .field {{ margin-bottom: 18px; }}

        label {{
            display: block;
            margin-bottom: 6px;
            font-size: 14px;
            font-weight: 600;
        }}

        .hint {{
            font-weight: 400;
            color: var(--muted);
        }}

        input {{
            width: 100%;
            padding: 11px 13px;
            font-size: 16px;
            font-family: inherit;
            color: var(--text);
            background: #fbfcfe;
            border: 1px solid var(--border);
            border-radius: 9px;
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }}

        input:focus {{
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
        }}

        button {{
            width: 100%;
            margin-top: 8px;
            padding: 13px 16px;
            font-size: 16px;
            font-weight: 600;
            font-family: inherit;
            color: #ffffff;
            background: var(--accent);
            border: none;
            border-radius: 9px;
            cursor: pointer;
            transition: background 0.15s ease;
        }}

        button:hover {{ background: var(--accent-dark); }}

        .results {{
            margin-top: 28px;
            padding-top: 24px;
            border-top: 1px solid var(--border);
        }}

        .results h2 {{
            margin: 0 0 16px;
            font-size: 17px;
        }}

        .row {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 16px;
            padding: 10px 0;
            border-bottom: 1px dashed var(--border);
        }}

        .row:last-child {{ border-bottom: none; }}

        .row .label {{ color: var(--muted); font-size: 15px; }}

        .row .value {{
            font-variant-numeric: tabular-nums;
            font-weight: 600;
            white-space: nowrap;
        }}

        .row.total .value {{
            color: var(--accent);
            font-size: 20px;
        }}

        .error {{
            margin-top: 24px;
            padding: 14px 16px;
            background: var(--error-bg);
            color: var(--error-text);
            border: 1px solid var(--error-border);
            border-radius: 9px;
            font-size: 14px;
        }}

        footer {{
            margin-top: 24px;
            color: var(--muted);
            font-size: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <main class="card">
        <h1>Ипотечный калькулятор</h1>
        <p class="subtitle">Аннуитетный платёж, итоговая сумма и переплата</p>

        <form method="post" action="/">
            <div class="field">
                <label for="amount">Сумма кредита, &#8381;</label>
                <input type="number" id="amount" name="amount" value="{amount}"
                       min="1" step="0.01" required placeholder="3000000">
            </div>
            <div class="field">
                <label for="annual_rate">
                    Годовая ставка, % <span class="hint">(0 — беспроцентный кредит)</span>
                </label>
                <input type="number" id="annual_rate" name="annual_rate" value="{annual_rate}"
                       min="0" step="0.01" required placeholder="12.5">
            </div>
            <div class="field">
                <label for="years">Срок, лет</label>
                <input type="number" id="years" name="years" value="{years}"
                       min="1" step="1" required placeholder="20">
            </div>
            <button type="submit">Рассчитать</button>
        </form>
        {results}
        <footer>Расчёт носит справочный характер и не является офертой.</footer>
    </main>
</body>
</html>
"""

# Строка с итогами расчёта, подставляемая в шаблон страницы.
RESULTS_TEMPLATE = """
        <section class="results">
            <h2>Результаты расчёта</h2>
            <div class="row total">
                <span class="label">Ежемесячный платёж</span>
                <span class="value">{monthly_payment} &#8381;</span>
            </div>
            <div class="row">
                <span class="label">Сумма кредита</span>
                <span class="value">{amount} &#8381;</span>
            </div>
            <div class="row">
                <span class="label">Итоговая сумма выплат</span>
                <span class="value">{total_payment} &#8381;</span>
            </div>
            <div class="row">
                <span class="label">Переплата по процентам</span>
                <span class="value">{overpayment} &#8381;</span>
            </div>
            <div class="row">
                <span class="label">Количество платежей</span>
                <span class="value">{months}</span>
            </div>
        </section>
"""

ERROR_TEMPLATE = '<div class="error">{message}</div>'


def _format_money(value: float) -> str:
    """Отформатировать денежную сумму с разделителями разрядов."""
    return f"{value:,.2f}".replace(",", " ")


def render_page(
    amount: str = "",
    annual_rate: str = "",
    years: str = "",
    results: str = "",
) -> str:
    """Собрать HTML-страницу с формой и (опционально) блоком результатов."""
    return PAGE_TEMPLATE.format(
        amount=escape(amount, quote=True),
        annual_rate=escape(annual_rate, quote=True),
        years=escape(years, quote=True),
        results=results,
    )


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    """Форма ввода параметров ипотеки."""
    return HTMLResponse(content=render_page())


@app.post("/", response_class=HTMLResponse)
def calculate(
    amount: float = Form(..., description="Сумма кредита"),
    annual_rate: float = Form(..., description="Годовая ставка, %"),
    years: int = Form(..., description="Срок кредита в годах"),
) -> HTMLResponse:
    """Принять параметры из формы и вернуть страницу с результатами расчёта."""
    try:
        result = calculate_mortgage(amount, annual_rate, years)
    except ValueError as exc:
        content = render_page(
            amount=str(amount),
            annual_rate=str(annual_rate),
            years=str(years),
            results=ERROR_TEMPLATE.format(message=escape(str(exc))),
        )
        return HTMLResponse(content=content, status_code=400)

    results = RESULTS_TEMPLATE.format(
        monthly_payment=_format_money(result["monthly_payment"]),
        amount=_format_money(amount),
        total_payment=_format_money(result["total_payment"]),
        overpayment=_format_money(result["overpayment"]),
        months=result["months"],
    )
    content = render_page(
        amount=str(amount),
        annual_rate=str(annual_rate),
        years=str(years),
        results=results,
    )
    return HTMLResponse(content=content)
