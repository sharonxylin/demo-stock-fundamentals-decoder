"""Business fundamentals data processing."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import yfinance as yf

from services.utils import money_formatting, percent_formatting, price_formatting


@dataclass
class FundamentalsSnapshot:
    """Display-ready fundamental metrics."""

    price_value: Optional[float]
    week_high_value: Optional[float]
    week_low_value: Optional[float]
    price_display: str
    price_date: Optional[str]
    fifty_two_week_high: str
    fifty_two_week_low: str
    fifty_two_week_change: str
    volume_display: str
    beta_display: str
    pe: str
    eps: str
    peg: str
    dividend_yield: str
    market_cap: str
    revenue: str
    revenue_growth: str
    operating_margin: str
    free_cash_flow: str
    debt_to_equity: str


def compute_fundamentals(stock: yf.Ticker, info: dict) -> FundamentalsSnapshot:
    """Aggregate financial statement metrics into a snapshot."""
    price = info.get("regularMarketPrice") or info.get("currentPrice")
    price_display = price_formatting(price)
    price_value = float(price) if isinstance(price, (int, float)) else None
    price_time = info.get("regularMarketTime")
    price_date = None
    if isinstance(price_time, (int, float)):
        price_date = datetime.fromtimestamp(price_time).strftime("%b %d, %Y")

    pe_raw = info.get("trailingPE")
    pe = f"{float(pe_raw):.2f}" if isinstance(pe_raw, (int, float)) else "N/A"
    eps = info.get("trailingEps", "N/A")
    peg = info.get("pegRatio", "N/A")
    market_cap = info.get("marketCap", "N/A")
    market_cap_display = money_formatting(market_cap)

    dividend_yield_raw = info.get("dividendYield")
    if isinstance(dividend_yield_raw, (int, float)):
        dy_value = (
            dividend_yield_raw * 100 if abs(dividend_yield_raw) < 0.2 else dividend_yield_raw
        )
        dividend_yield = percent_formatting(dy_value, decimals=2)
    else:
        dividend_yield = "N/A"

    week_high_raw = info.get("fiftyTwoWeekHigh")
    week_low_raw = info.get("fiftyTwoWeekLow")
    week_high_value = float(week_high_raw) if isinstance(week_high_raw, (int, float)) else None
    week_low_value = float(week_low_raw) if isinstance(week_low_raw, (int, float)) else None
    fifty_two_week_high = price_formatting(week_high_raw)
    fifty_two_week_low = price_formatting(week_low_raw)
    volume = info.get("regularMarketVolume")
    volume_display = f"{int(volume):,}" if isinstance(volume, (int, float)) else "N/A"

    beta = info.get("beta")
    try:
        beta_display = f"{float(beta):.2f}" if beta is not None else "N/A"
    except Exception:
        beta_display = "N/A"

    fifty_two_week_change = info.get("52WeekChange")
    week_change_pct = None
    if isinstance(fifty_two_week_change, (int, float)):
        week_change_pct = fifty_two_week_change * 100
    fifty_two_week_change_display = percent_formatting(week_change_pct)

    latest_rev = prev_rev = revenue_growth = None
    operating_margin = None
    fcf = None
    debt_to_equity = None

    try:
        fin = stock.financials
        if not fin.empty:
            rev_series = fin.loc["Total Revenue"]
            latest_rev = float(rev_series.iloc[0])
            if len(rev_series) > 1:
                prev_rev = float(rev_series.iloc[1])
            if prev_rev and prev_rev != 0:
                revenue_growth = (latest_rev - prev_rev) / prev_rev * 100

            op_income = float(fin.loc["Operating Income"].iloc[0])
            if latest_rev and latest_rev != 0:
                operating_margin = op_income / latest_rev * 100
    except Exception:
        pass

    try:
        cf = stock.cashflow
        if not cf.empty:
            op_cf = float(cf.loc["Total Cash From Operating Activities"].iloc[0])
            capex = float(cf.loc["Capital Expenditures"].iloc[0])
            fcf = op_cf + capex
    except Exception:
        pass

    try:
        bs = stock.balance_sheet
        if not bs.empty:
            total_debt = float(bs.loc["Total Debt"].iloc[0])
            total_equity = float(bs.loc["Total Stockholder Equity"].iloc[0])
            if total_equity != 0:
                debt_to_equity = total_debt / total_equity
    except Exception:
        pass

    dte_display = (
        f"{debt_to_equity:.2f}x" if isinstance(debt_to_equity, (int, float)) else "N/A"
    )

    return FundamentalsSnapshot(
        price_value=price_value,
        week_high_value=week_high_value,
        week_low_value=week_low_value,
        price_display=price_display,
        price_date=price_date,
        fifty_two_week_high=fifty_two_week_high,
        fifty_two_week_low=fifty_two_week_low,
        fifty_two_week_change=fifty_two_week_change_display,
        volume_display=volume_display,
        beta_display=beta_display,
        pe=pe,
        eps=eps,
        peg=peg,
        dividend_yield=dividend_yield,
        market_cap=market_cap_display,
        revenue=money_formatting(latest_rev),
        revenue_growth=percent_formatting(revenue_growth),
        operating_margin=percent_formatting(operating_margin),
        free_cash_flow=money_formatting(fcf),
        debt_to_equity=dte_display,
    )


def build_pdf_context(
    snapshot: FundamentalsSnapshot,
    header_line: str,
    badge_lines: List[str],
    *,
    slider_details: Optional[Dict[str, Any]] = None,
    history_points: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Return the context dict consumed by the PDF builder."""
    return {
        "currentPriceFormatted": snapshot.price_display,
        "fiftyTwoWeekHighFormatted": snapshot.fifty_two_week_high,
        "fiftyTwoWeekLowFormatted": snapshot.fifty_two_week_low,
        "betaFormatted": snapshot.beta_display,
        "fiftyTwoWeekChangeFormatted": snapshot.fifty_two_week_change,
        "volumeFormatted": snapshot.volume_display,
        "peFormatted": snapshot.pe,
        "pegFormatted": snapshot.peg,
        "epsFormatted": snapshot.eps,
        "dividendYieldFormatted": snapshot.dividend_yield,
        "marketCapFormatted": snapshot.market_cap,
        "revenueFormatted": snapshot.revenue,
        "revenueGrowthFormatted": snapshot.revenue_growth,
        "operatingMarginFormatted": snapshot.operating_margin,
        "fcfFormatted": snapshot.free_cash_flow,
        "debtToEquityFormatted": snapshot.debt_to_equity,
        "header_line": header_line,
        "badge_lines": badge_lines,
        "slider": slider_details,
        "history_points": history_points,
    }


__all__ = ["FundamentalsSnapshot", "compute_fundamentals", "build_pdf_context"]
