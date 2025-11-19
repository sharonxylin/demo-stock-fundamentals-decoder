"""Reusable Streamlit sections."""
from __future__ import annotations

from typing import List, Optional

import plotly.graph_objects as go
import streamlit as st

from services.metrics import METRICS, explain
from services.company_profile import CompanyProfile
from services.constants import DISCLAIMER_TEXT
from services.fundamentals import FundamentalsSnapshot


def render_company_identity(profile: CompanyProfile) -> None:
    """Display the company logo, name, and metadata."""
    details_html = (
        "<div style=\"font-size:0.9rem; color:#666; margin:0;\">"
        f"Ticker: {profile.ticker} • Sector: {profile.sector} • Industry: {profile.industry}"
        "</div>"
    )

    if profile.logo_url:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.75rem;">
                <img src="{profile.logo_url}" style="height:40px; border-radius:8px;" />
                <div>
                    <div style="font-size:1.4rem; font-weight:600; margin:0;">{profile.name}</div>
                    {details_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="margin-bottom:0.75rem;">
                <div style="font-size:1.4rem; font-weight:600; margin:0;">{profile.name}</div>
                {details_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    for caption in profile.caption_lines:
        st.markdown(
            f"<div style='font-size:0.9rem; color:#2c7be5; margin-bottom:0.35rem;'>{caption}</div>",
            unsafe_allow_html=True,
        )


def render_price_snapshot(snapshot: FundamentalsSnapshot) -> Optional[dict]:
    """Show price metrics and slider. Returns slider details for PDF context."""
    st.subheader("Price snapshot")
    price_col1, price_col2, price_col3 = st.columns(3)
    with price_col1:
        st.metric(METRICS["share_price"]["name"], snapshot.price_display, help=explain("share_price"))
        if snapshot.price_date:
            st.caption(f"Updated {snapshot.price_date}")
    with price_col2:
        st.metric(METRICS["52_week_high"]["name"], snapshot.fifty_two_week_high, help=explain("52_week_high"))
    with price_col3:
        st.metric(METRICS["52_week_low"]["name"], snapshot.fifty_two_week_low, help=explain("52_week_low"))

    slider_details = None
    if (
        isinstance(snapshot.week_low_value, (int, float))
        and isinstance(snapshot.week_high_value, (int, float))
        and isinstance(snapshot.price_value, (int, float))
        and snapshot.week_high_value > snapshot.week_low_value
    ):
        try:
            pos = (snapshot.price_value - snapshot.week_low_value) / (
                snapshot.week_high_value - snapshot.week_low_value
            )
            pos = max(0.0, min(1.0, pos))
            slider_details = {
                "low_formatted": snapshot.fifty_two_week_low,
                "high_formatted": snapshot.fifty_two_week_high,
                "price_formatted": snapshot.price_display,
                "position": pos,
            }
            st.markdown(
                f"""
                <div style="margin-top:0.35rem; margin-bottom:0.6rem; padding:0.4rem 0.6rem; border-radius:8px; background:#fafafa;">
                    <div style="display:flex; justify-content:space-between; font-size:0.78rem; color:#666; padding:0 0.15rem;">
                        <span>{snapshot.fifty_two_week_low}</span>
                        <span>{snapshot.fifty_two_week_high}</span>
                    </div>
                    <div style="position:relative; height:4px; background:#eee; border-radius:999px; margin:0.18rem 0.25rem;">
                        <div style="position:absolute; inset:0; background:#e0e0e0; border-radius:999px;"></div>
                        <div style="position:absolute; top:-3px; left:{pos*100:.1f}%; transform:translateX(-50%); width:10px; height:10px; border-radius:999px; background:#2c7be5;"></div>
                    </div>
                    <div style="text-align:center; font-size:0.78rem; color:#444; margin-top:0.05rem; padding:0 0.15rem;">
                        Current price: {snapshot.price_display}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception:
            pass

    return slider_details


def render_price_history(stock) -> Optional[List[float]]:
    """Render the 1-year price history chart and return the close values."""
    try:
        hist_data = stock.history(period="1y")
        if hist_data.empty:
            return None
        history_points = [float(value) for value in hist_data["Close"].tolist()]
        st.markdown("**Historical Market Price – Past 1 Year**")
        first_close = hist_data["Close"].iloc[0]
        last_close = hist_data["Close"].iloc[-1]
        if last_close > first_close:
            line_color = "#2ecc71"
        elif last_close < first_close:
            line_color = "#e74c3c"
        else:
            line_color = "#95a5a6"
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=hist_data.index,
                y=hist_data["Close"],
                mode="lines",
                name="Close Price",
                line=dict(color=line_color, width=2),
            )
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Close Price (USD)",
            margin=dict(l=40, r=40, t=40, b=40),
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)
        return history_points
    except Exception as exc:
        st.warning(f"Unable to load historical chart: {exc}")
        return None


def render_market_behavior(snapshot: FundamentalsSnapshot) -> None:
    """Show beta, 52-week performance, and volume metrics."""
    st.subheader("Market behavior")
    market_col1, market_col2, market_col3 = st.columns(3)
    with market_col1:
        st.metric(METRICS["beta"]["name"], snapshot.beta_display, help=explain("beta"))
    with market_col2:
        st.metric(
            METRICS["52_week_change"]["name"],
            snapshot.fifty_two_week_change,
            help=explain("52_week_change"),
        )
    with market_col3:
        st.metric(METRICS["volume"]["name"], snapshot.volume_display, help=explain("volume"))


def render_fundamentals_section(snapshot: FundamentalsSnapshot) -> None:
    """Display valuation and business quality metrics."""
    st.subheader("Fundamentals snapshot")
    st.markdown("**Valuation metrics**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(METRICS["pe_ratio"]["name"], snapshot.pe, help=explain("pe_ratio"))
        st.metric(METRICS["eps"]["name"], snapshot.eps, help=explain("eps"))
    with col2:
        st.metric(METRICS["peg_ratio"]["name"], snapshot.peg, help=explain("peg_ratio"))
        st.metric(
            METRICS["dividend_yield"]["name"],
            snapshot.dividend_yield,
            help=explain("dividend_yield"),
        )
    with col3:
        st.metric(METRICS["market_cap"]["name"], snapshot.market_cap, help=explain("market_cap"))

    st.markdown("**Business quality metrics**")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(METRICS["revenue"]["name"], snapshot.revenue, help=explain("revenue"))
        st.metric(
            METRICS["revenue_growth_yoy"]["name"],
            snapshot.revenue_growth,
            help=explain("revenue_growth_yoy"),
        )
    with col_b:
        st.metric(
            METRICS["operating_margin"]["name"],
            snapshot.operating_margin,
            help=explain("operating_margin"),
        )
        st.metric(
            METRICS["free_cash_flow"]["name"],
            snapshot.free_cash_flow,
            help=explain("free_cash_flow"),
        )
    with col_c:
        st.metric(
            METRICS["debt_to_equity"]["name"],
            snapshot.debt_to_equity,
            help=explain("debt_to_equity"),
        )


def render_company_summary(profile: CompanyProfile) -> None:
    """Show the long business summary."""
    st.caption(f"Company Summary: {profile.summary}")


def render_footer() -> None:
    """Render the global footer."""
    st.markdown(
        f"""
        <div class="app-footer">
            <hr />
            <div>Stock Fundamentals Decoder App Made by Sharon Lin</div>
            <div class="footer-disclaimer">
                <strong>Disclaimer:</strong>
                {DISCLAIMER_TEXT}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


__all__ = [
    "render_company_identity",
    "render_price_snapshot",
    "render_price_history",
    "render_market_behavior",
    "render_fundamentals_section",
    "render_company_summary",
    "render_footer",
]
