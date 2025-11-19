"""Helpers for building company profile metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import yfinance as yf

from services.utils import fetch_logo


@dataclass
class CompanyProfile:
    """Structured representation of company metadata for display."""

    name: str
    ticker: str
    sector: str
    industry: str
    summary: str
    logo_url: Optional[str]
    caption_lines: List[str] = field(default_factory=list)


def build_company_profile(
    stock: yf.Ticker, info: dict, fallback_ticker: str
) -> CompanyProfile:
    """Construct a company profile from Yahoo Finance metadata."""
    resolved_ticker = (stock.ticker or fallback_ticker).upper()
    company = info.get("longName", resolved_ticker)
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    company_summary = info.get("longBusinessSummary", "N/A")
    caption_lines = _build_industry_badges(
        resolved_ticker, industry, info.get("industryKey")
    )
    logo_url = fetch_logo(resolved_ticker, info)

    return CompanyProfile(
        name=company,
        ticker=resolved_ticker,
        sector=sector,
        industry=industry,
        summary=company_summary,
        logo_url=logo_url,
        caption_lines=caption_lines,
    )


def _build_industry_badges(ticker: str, industry: str, industry_key: Optional[str]):
    caption_lines: List[str] = []
    if not industry_key:
        return caption_lines

    try:
        industry_obj = yf.Industry(industry_key)
        top_companies_df = getattr(industry_obj, "top_companies", None)
        top_growth_df = getattr(industry_obj, "top_growth_companies", None)
        top_perf_df = getattr(industry_obj, "top_performing_companies", None)
        if top_companies_df is not None and ticker in top_companies_df.index:
            caption_lines.append(
                f"🔝 <b>One of the Top Companies</b> in the {industry} industry"
            )
        if top_growth_df is not None and ticker in top_growth_df.index:
            caption_lines.append(
                f"📈 <b>One of the Top Growth Companies</b> in the {industry} industry"
            )
        if top_perf_df is not None and ticker in top_perf_df.index:
            caption_lines.append(
                f"🌟 <b>One of the Top Performing Companies</b> in the {industry} industry"
            )
    except Exception:
        pass
    return caption_lines


__all__ = ["CompanyProfile", "build_company_profile"]
