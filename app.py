import streamlit as st
import pandas as pd
import plotly.express as px
from services.ai_service import generate_company_insights
from services.utils import PDF_SUPPORTED, build_pdf
from services.company_profile import build_company_profile
from services.fundamentals import build_pdf_context, compute_fundamentals
from services.portfolio_composition import (
    FundCompositionUnavailableError,
    InvalidFundTickerError,
    fetch_portfolio_composition,
)
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


def _render_query_form():
    """Render the hero inputs and return ticker/model/submit state."""
    left_pad, center_column, right_pad = st.columns([1, 2, 1])
    with center_column:
        query = st.text_input(
            "Enter stock ticker (e.g., AAPL, MSFT) (NYSE tickers only):",
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
        action_col, model_col = st.columns([1.2, 1])
        with action_col:
            learn_clicked = st.button("Learn About This Company")
        with model_col:
            model_options = {
                "GPT-5 mini": "gpt-5-mini",
                "GPT-5.1": "gpt-5.1",
            }
            selected_model_label = st.selectbox(
                "AI model",
                list(model_options.keys()),
                index=0,
            )
            selected_model = model_options[selected_model_label]
        if st.session_state.pop("auto_learn_submit", False) and ticker:
            learn_clicked = True

        st.markdown(
            '<div class="hero-disclaimer"><p>This is educational content, not financial advice.</p></div>',
            unsafe_allow_html=True,
        )
    return ticker, selected_model, learn_clicked


def _render_company_columns(profile, fundamentals, stock):
    """Render the left/right analysis columns and return placeholders."""
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
        pdf_container = st.container()
        _render_insights_panel(
            insights_placeholder,
            profile.name,
            "<div class='insights-panel__loading'>Preparing AI insights...</div>",
        )
    return slider_details, history_points, insights_placeholder, pdf_container


def _display_insights(profile, fundamentals, selected_model, placeholder):
    """Call the AI service and render the resulting markdown/HTML."""
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
        model=selected_model,
    )

    if md:
        insights_html = md.markdown(insights_text)
        _render_insights_panel(
            placeholder,
            profile.name,
            insights_html,
        )
    else:
        body_html = "<div>{}</div>".format(insights_text.replace("\n", "<br/>"))
        _render_insights_panel(
            placeholder,
            profile.name,
            body_html,
        )
    return insights_text

def _render_pdf_controls(
    container,
    profile,
    fundamentals,
    slider_details,
    history_points,
    insights_text,
):
    """Render the PDF download button (if supported)."""
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
    with container:
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


def _render_analysis(profile, fundamentals, stock, selected_model):
    """Render the full analysis view, returning True when a footer was drawn."""
    (
        slider_details,
        history_points,
        insights_placeholder,
        pdf_container,
    ) = _render_company_columns(profile, fundamentals, stock)

    with st.container():
        render_footer()

    insights_text = _display_insights(profile, fundamentals, selected_model, insights_placeholder)
    _render_pdf_controls(
        pdf_container,
        profile,
        fundamentals,
        slider_details,
        history_points,
        insights_text,
    )
    return True


def _render_company_analysis_tab():
    """Render the Company Analysis tab."""
    ticker, selected_model, learn_clicked = _render_query_form()
    footer_rendered = False

    if learn_clicked:
        if ticker:
            try:
                stock, info = resolve_stock_and_info(ticker)
                profile = build_company_profile(stock, info, ticker)
                fundamentals = compute_fundamentals(stock, info)
                footer_rendered = _render_analysis(profile, fundamentals, stock, selected_model)
            except IndexFundTickerError:
                st.warning(INDEX_FUND_MESSAGE)
            except InvalidTickerError:
                st.warning(INVALID_TICKER_MESSAGE)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a ticker")

    if not footer_rendered:
        render_footer()


def _render_portfolio_holdings(composition) -> None:
    """Render the holdings table for the fund composition tab."""
    st.markdown(
        f"**Top holdings for {composition.fund_name} ({composition.fund_symbol})**"
    )

    top_holdings = composition.holdings[:15]
    pie_rows = []
    for idx, holding in enumerate(top_holdings):
        label = holding.symbol or holding.name or f"Holding {idx + 1}"
        pie_rows.append({"label": label, "percent": max(holding.percent, 0.0)})

    total_percent = sum(row["percent"] for row in pie_rows)
    remaining = max(0.0, 100.0 - total_percent)
    if remaining > 0.01:
        pie_rows.append({"label": "Others", "percent": remaining})

    chart_total = sum(row["percent"] for row in pie_rows)
    if chart_total > 0:
        fig = px.pie(
            pie_rows,
            names="label",
            values="percent",
            hole=0.35,
            color="label",
            color_discrete_map={"Others": "#f2f2f2"},
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Holdings percentages are missing; pie chart not available.")

    records = [
        {
            "Symbol": holding.symbol or "—",
            "Name": holding.name or "—",
            "Portfolio %": holding.percent_display,
        }
        for holding in composition.holdings
    ]
    df = pd.DataFrame(records)
    editor_state_key = "holdings_table_editor"
    st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        disabled=True,
        key=editor_state_key,
    )

    selection_state = st.session_state.get(editor_state_key, {})
    selected_rows = selection_state.get("selection", {}).get("rows", []) if isinstance(selection_state, dict) else []
    last_handled_row = st.session_state.get("last_handled_holding_row")
    if selected_rows:
        selected_idx = selected_rows[-1]
        if selected_idx != last_handled_row and 0 <= selected_idx < len(composition.holdings):
            st.session_state["last_handled_holding_row"] = selected_idx
            target_ticker = (composition.holdings[selected_idx].symbol or "").strip().upper()
            if target_ticker:
                st.session_state["company_query_input"] = target_ticker
                st.session_state["auto_learn_submit"] = True
                st.experimental_rerun()


def _render_portfolio_tab():
    """Render the Portfolio Composition tab."""
    st.write("Enter an index fund, ETF, or mutual fund ticker to view its reported holdings.")
    fund_ticker = st.text_input(
        "Fund ticker:",
        key="fund_composition_ticker",
        placeholder="VOO",
    )
    show_composition = st.button("Show Portfolio Composition")

    if show_composition:
        if not fund_ticker:
            st.warning("Please enter a fund ticker.")
            return
        try:
            composition = fetch_portfolio_composition(fund_ticker)
            _render_portfolio_holdings(composition)
        except InvalidFundTickerError as exc:
            st.warning(str(exc) or "This ticker does not look like an ETF or mutual fund.")
        except FundCompositionUnavailableError as exc:
            st.error(str(exc) or "Could not retrieve holdings for this fund.")
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")

    render_footer()


def main():
    configure_page()
    st.title("📈 Stock Fundamentals Decoder")
    st.write("For index fund investors curious about individual companies")
    company_tab, portfolio_tab = st.tabs(["🏢 Company Analysis", "📊 Portfolio Composition"])
    with company_tab:
        _render_company_analysis_tab()
    with portfolio_tab:
        _render_portfolio_tab()


if __name__ == "__main__":
    main()
