"""Ticker lookup helpers and validation logic."""
from __future__ import annotations

from typing import Optional, Tuple

import requests
import yfinance as yf


class InvalidTickerError(Exception):
    """Raised when Yahoo Finance cannot find the requested ticker."""


class IndexFundTickerError(Exception):
    """Raised when the input corresponds to an ETF or index fund."""


INVALID_TICKER_MESSAGE = (
    "We couldn’t find that company. Try entering a **ticker symbol "
    "(not the full company name)** — like AAPL, MSFT, or META."
)
INDEX_FUND_MESSAGE = (
    "This is an index fund/ETF. Try an individual company like AAPL or MSFT."
)
YAHOO_SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"
INDEX_FUND_QUOTE_TYPES = {"ETF", "INDEX", "MUTUALFUND"}


def lookup_symbol_by_name(query: str) -> Optional[str]:
    """Use Yahoo's search API to map a company name to its ticker symbol."""
    try:
        response = requests.get(
            YAHOO_SEARCH_URL,
            params={"q": query, "quotesCount": 1, "newsCount": 0},
            timeout=4,
        )
        data = response.json()
        for quote in data.get("quotes", []):
            symbol = quote.get("symbol")
            quote_type = quote.get("quoteType")
            if symbol and quote_type in {"EQUITY", "ETF"}:
                return symbol.upper()
    except Exception:
        pass
    return None


def safe_fetch_info(symbol: str) -> Tuple[Optional[yf.Ticker], Optional[dict]]:
    """Return (Ticker, info) if symbol is valid, otherwise (None, None)."""
    ticker_obj = yf.Ticker(symbol)
    try:
        info = ticker_obj.info
    except Exception:
        return None, None

    if not info:
        return None, None

    if info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
        return None, None

    return ticker_obj, info


def resolve_stock_and_info(user_input: str) -> Tuple[yf.Ticker, dict]:
    """Resolve either a ticker or company name into a ticker object and info."""
    cleaned = (user_input or "").strip()
    if not cleaned:
        raise InvalidTickerError

    candidates = []

    def enqueue(symbol: Optional[str]):
        if not symbol:
            return
        symbol_upper = symbol.upper()
        if symbol_upper not in candidates:
            candidates.append(symbol_upper)

    enqueue(cleaned)

    suggestion = lookup_symbol_by_name(cleaned)
    enqueue(suggestion)

    for candidate in candidates:
        ticker_obj, info = safe_fetch_info(candidate)
        if info:
            quote_type = str(info.get("quoteType") or "").upper()
            is_fund = bool(info.get("isFund"))
            if quote_type in INDEX_FUND_QUOTE_TYPES or is_fund:
                raise IndexFundTickerError
            return ticker_obj, info

    raise InvalidTickerError


__all__ = [
    "lookup_symbol_by_name",
    "safe_fetch_info",
    "resolve_stock_and_info",
    "InvalidTickerError",
    "IndexFundTickerError",
    "INVALID_TICKER_MESSAGE",
    "INDEX_FUND_MESSAGE",
]
