"""Helpers to fetch index fund/ETF/mutual fund holdings."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import yahooquery as yq
import yfinance as yf

from services.ticker_service import INDEX_FUND_QUOTE_TYPES


class InvalidFundTickerError(Exception):
    """Raised when the given ticker is not an index fund/ETF/mutual fund."""


class FundCompositionUnavailableError(Exception):
    """Raised when holdings data cannot be retrieved."""


@dataclass
class Holding:
    """Single portfolio holding entry."""

    symbol: str
    name: str
    percent: float

    @property
    def percent_display(self) -> str:
        """Return a friendly percent string (e.g., 4.2%)."""
        try:
            return f"{self.percent:.2f}%"
        except Exception:
            return "N/A"


@dataclass
class PortfolioComposition:
    """Portfolio composition response."""

    fund_symbol: str
    fund_name: str
    holdings: List[Holding]


def _validate_fund_ticker(symbol: str) -> tuple[str, str]:
    """Verify ticker is an index fund/ETF/mutual fund and return name."""
    ticker_obj = yf.Ticker(symbol)
    try:
        info = ticker_obj.info
    except Exception as exc:
        raise InvalidFundTickerError(str(exc))

    if not info:
        raise InvalidFundTickerError("No data returned for ticker.")

    quote_type = str(info.get("quoteType") or "").upper()
    is_fund = bool(info.get("isFund"))
    if quote_type not in INDEX_FUND_QUOTE_TYPES and not is_fund:
        raise InvalidFundTickerError("Ticker is not an index fund/ETF/mutual fund.")

    fund_name = info.get("longName") or info.get("shortName") or symbol.upper()
    return symbol.upper(), fund_name


def _normalize_percent(raw_value: Optional[float]) -> Optional[float]:
    """Normalize holdingPercent to a 0–100 percentage float."""
    if raw_value is None:
        return None
    try:
        value = float(raw_value)
        if abs(value) <= 1:
            value *= 100
        return value
    except Exception:
        return None


def fetch_portfolio_composition(symbol: str) -> PortfolioComposition:
    """
    Fetch holdings for an index fund/ETF/mutual fund ticker using yahooquery.

    Returns a PortfolioComposition with normalized percentages.
    """
    clean_symbol = (symbol or "").strip().upper()
    if not clean_symbol:
        raise InvalidFundTickerError("Please provide a ticker.")

    fund_symbol, fund_name = _validate_fund_ticker(clean_symbol)

    try:
        fund = yq.Ticker(fund_symbol)
        fund_data = fund.fund_holding_info
    except Exception as exc:
        raise FundCompositionUnavailableError(str(exc))

    if not isinstance(fund_data, dict) or fund_symbol not in fund_data:
        raise FundCompositionUnavailableError("No holdings data found for ticker.")

    raw_holdings = fund_data[fund_symbol].get("holdings") or []
    holdings: List[Holding] = []

    for item in raw_holdings:
        percent = _normalize_percent(item.get("holdingPercent"))
        entry = Holding(
            symbol=item.get("symbol") or "",
            name=item.get("holdingName") or "",
            percent=percent if percent is not None else 0.0,
        )
        holdings.append(entry)

    if not holdings:
        raise FundCompositionUnavailableError("Holdings payload was empty.")

    holdings.sort(key=lambda h: h.percent, reverse=True)
    return PortfolioComposition(fund_symbol=fund_symbol, fund_name=fund_name, holdings=holdings)


__all__ = [
    "fetch_portfolio_composition",
    "PortfolioComposition",
    "Holding",
    "InvalidFundTickerError",
    "FundCompositionUnavailableError",
]
