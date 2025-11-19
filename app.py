import streamlit as st
from services.ai_service import generate_company_insights
from services.utils import PDF_SUPPORTED, build_pdf
from services.company_profile import build_company_profile
from services.fundamentals import build_pdf_context, compute_fundamentals
from services.ticker_service import (
    INDEX_FUND_MESSAGE,
    INVALID_TICKER_MESSAGE,
    IndexFundTickerError,
    InvalidTickerError,
    lookup_symbol_by_name,
    resolve_stock_and_info,
)
from ui.sections import (
    render_company_identity,
    render_company_summary,
    render_footer,
    render_fundamentals_section,
    render_market_behavior,
    render_price_history,
    render_price_snapshot,
)
from ui.styles import configure_page

try:
    import markdown as md
except ImportError:
    md = None


def _trigger_learn_submit():
    """Signal that Enter was pressed inside the ticker input."""
    st.session_state["auto_learn_submit"] = True


def _render_insights_panel(placeholder, company: str, body_html: str) -> None:
    """Render the insights panel shell with branding and disclaimer."""
    placeholder.markdown(
        f"""
        <div class="insights-box insights-panel">
            <div class="insights-panel__title">💡 AI-generated insights for {company}</div>
            <div class="insights-panel__body">{body_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

configure_page()

# app main logic
left_pad, center_column, right_pad = st.columns([1, 2, 1])
with center_column:
    st.title("📈 Stock Fundamentals Decoder")
    st.write("For index fund investors curious about individual companies")
    query = st.text_input(
        "Enter stock ticker (e.g., AAPL, MSFT):",
        key="company_query_input",
        on_change=_trigger_learn_submit,
        placeholder="AAPL",

    )
    suggestion = None
    if query and len(query.strip()) >= 2:
        try:
            lookup_result = lookup_symbol_by_name(query.strip())
            if lookup_result:
                suggestion = st.selectbox(
                    "Did you mean:",
                    [lookup_result, query.strip()],
                    format_func=lambda v: v.upper(),
                )
        except Exception:
            pass
    ticker_input = suggestion or query
    ticker = (ticker_input or "").strip().upper()
    learn_clicked = st.button("Learn About This Company")
    if st.session_state.pop("auto_learn_submit", False) and ticker:
        learn_clicked = True

    st.markdown(
        '<div class="hero-disclaimer">This is educational content, not financial advice.</div>',
        unsafe_allow_html=True,
    )

if learn_clicked:
    if ticker:
        try:
            stock, info = resolve_stock_and_info(ticker)
            profile = build_company_profile(stock, info, ticker)
            fundamentals = compute_fundamentals(stock, info)

            left_col, right_col = st.columns([3, 2])
            with left_col:
                render_company_identity(profile)
                slider_details = render_price_snapshot(fundamentals)
                history_points = render_price_history(stock)
                render_market_behavior(fundamentals)
                render_fundamentals_section(fundamentals)
                render_company_summary(profile)

            with right_col:
                insights_placeholder = st.empty()
                _render_insights_panel(
                    insights_placeholder,
                    profile.name,
                    "<div class='insights-panel__loading'>Preparing AI insights...</div>",
                )
                insights_text = generate_company_insights(
                    company=profile.name,
                    ticker=profile.ticker,
                    industry=profile.industry,
                    company_summary=profile.summary,
                    revenue=fundamentals.revenue,
                    revenue_growth=fundamentals.revenue_growth,
                    operating_margin=fundamentals.operating_margin,
                    free_cash_flow=fundamentals.free_cash_flow,
                    debt_to_equity=fundamentals.debt_to_equity,
                    pe=fundamentals.pe,
                    eps=fundamentals.eps,
                    peg=fundamentals.peg,
                    market_cap=fundamentals.market_cap,
                    dividend_yield=fundamentals.dividend_yield,
                    beta=fundamentals.beta_display,
                )

                if md:
                    insights_html = md.markdown(insights_text)
                    _render_insights_panel(
                        insights_placeholder,
                        profile.name,
                        insights_html,
                    )
                else:
                    body_html = "<div>{}</div>".format(
                        insights_text.replace("\n", "<br/>")
                    )
                    _render_insights_panel(
                        insights_placeholder,
                        profile.name,
                        body_html,
                    )

                header_line = (
                    f"Ticker: {profile.ticker} • Sector: {profile.sector} • Industry: {profile.industry}"
                )
                badge_text_lines = [
                    c.replace("<b>", "").replace("</b>", "") for c in profile.caption_lines
                ]
                pdf_context = build_pdf_context(
                    fundamentals,
                    header_line,
                    badge_text_lines,
                    slider_details=slider_details,
                    history_points=history_points,
                )
                pdf_bytes = build_pdf(profile.name, profile.ticker, insights_text, pdf_context)
                if pdf_bytes:
                    st.download_button(
                        label="Download this analysis as PDF",
                        data=pdf_bytes,
                        on_click="ignore",
                        file_name=f"{profile.name}_{profile.ticker}_fundamentals_ai_analysis.pdf",
                        mime="application/pdf",
                    )
                elif not PDF_SUPPORTED:
                    st.info("To enable PDF download, install the 'fpdf' package: `pip install fpdf`.")

        except IndexFundTickerError:
            st.warning(INDEX_FUND_MESSAGE)
        except InvalidTickerError:
            st.warning(INVALID_TICKER_MESSAGE)
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a ticker")

render_footer()
