"""Helper utilities for formatting values, fetching logos, and building PDFs."""
from __future__ import annotations
from pathlib import Path
import requests

# Optional PDF export support
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

from services.constants import DISCLAIMER_TEXT

PDF_SUPPORTED = FPDF is not None
UNICODE_FONT_PATH = None
if PDF_SUPPORTED:
    candidate_fonts = [
        Path(__file__).resolve().parent / "fonts" / "AppFont.ttf",
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]
    for candidate in candidate_fonts:
        if candidate.exists():
            UNICODE_FONT_PATH = candidate
            break

PDF_SUPPORTS_UNICODE = UNICODE_FONT_PATH is not None

# percentage formatting helper
def percent_formatting(value, decimals: int = 1) -> str:
    """Format numeric values as percentages, defaulting to N/A when missing."""
    try:
        if value is None:
            return "N/A"
        return f"{value:.{decimals}f}%"
    except Exception:
        return "N/A"

# money formatting helper
def money_formatting(value) -> str:
    """Format numeric values in millions, billions, or trillions."""
    try:
        if value is None:
            return "N/A"
        amount = float(value)
        if abs(amount) >= 1e12:
            return f"${amount/1e12:.1f}T"
        if abs(amount) >= 1e9:
            return f"${amount/1e9:.1f}B"
        return f"${amount/1e6:.1f}M"
    except Exception:
        return "N/A"

# price formatting helper. in USD.
def price_formatting(value) -> str:
    """Format numeric values as price strings."""
    try:
        if value is None:
            return "N/A"
        return f"${float(value):,.2f}"
    except Exception:
        return "N/A"

# fetch company logo from free sources
def fetch_logo(ticker: str, info: dict) -> str | None:
    """Fetch a company logo using free sources (Clearbit, Google favicon, Wikipedia)."""
    domain = None
    website = info.get("website") if isinstance(info, dict) else None
    if website:
        try:
            domain = website.split("//")[-1].split("/")[0].split("?")[0]
            clearbit_url = f"https://logo.clearbit.com/{domain}"
            resp = requests.get(clearbit_url, timeout=4)
            if resp.status_code == 200:
                return clearbit_url
        except Exception:
            pass

    if domain:
        try:
            google_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=256"
            resp = requests.get(google_url, timeout=4)
            if resp.status_code == 200:
                return google_url
        except Exception:
            pass

    company_name = None
    if isinstance(info, dict):
        company_name = info.get("longName") or info.get("shortName")
    if not company_name:
        company_name = ticker.upper()

    try:
        search_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "piprop": "thumbnail",
                "pithumbsize": 256,
                "generator": "search",
                "gsrsearch": company_name,
                "gsrlimit": 1,
            },
            timeout=5,
        )
        data = search_resp.json()
        pages = data.get("query", {}).get("pages", {})
        if pages:
            first_page = next(iter(pages.values()))
            thumb = first_page.get("thumbnail", {}).get("source")
            if thumb:
                return thumb
    except Exception:
        pass

    return None

# build a PDF report
def build_pdf(company: str, ticker: str, insights_text: str, info: dict | None = None) -> bytes | None:
    """
    Build a PDF report that mirrors the Streamlit layout, with the metrics stack on the left
    (Price snapshot, Market behavior, Fundamentals snapshot) and the AI insights column
    on the right. `info` must contain preformatted strings for each displayed metric.
    """
    if FPDF is None:
        return None
    info = info or {}

    unicode_enabled = PDF_SUPPORTS_UNICODE and UNICODE_FONT_PATH is not None

    def pdf_safe(text: str) -> str:
        if not isinstance(text, str):
            text = str(text)
        text = text.replace("\r", "\n")
        replacements = {
            "—": "-",
            "–": "-",
            "•": "-",
            "’": "'",
            "‘": "'",
            "“": '"',
            "”": '"',
        }
        for bad, repl in replacements.items():
            text = text.replace(bad, repl)
        text = text.replace("\n\n", "\n")
        text = text.replace("**", "")  # Remove markdown bold artifacts
        if not unicode_enabled:
            text = text.encode("latin-1", errors="ignore").decode("latin-1")
        return text

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_family = "Arial"
    if unicode_enabled and UNICODE_FONT_PATH:
        try:
            pdf.add_font("AppFont", "", str(UNICODE_FONT_PATH), uni=True)
            pdf.add_font("AppFont", "B", str(UNICODE_FONT_PATH), uni=True)
            font_family = "AppFont"
        except Exception:
            unicode_enabled = False

    pdf.set_font(font_family, "B", 16)
    pdf.cell(0, 10, pdf_safe(f"{company} ({ticker.upper()})"), ln=True)

    pdf.set_font(font_family, "", 11)
    pdf.ln(3)
    pdf.multi_cell(0, 6, pdf_safe("AI-generated fundamentals explainer for index fund investors."), align="L")

    header_line = info.get("header_line")
    if header_line:
        pdf.set_font(font_family, "", 11)
        pdf.ln(1)
        pdf.multi_cell(0, 6, pdf_safe(header_line))

    badge_lines = info.get("badge_lines") or []
    if badge_lines:
        pdf.set_text_color(44, 123, 229)
        pdf.set_font(font_family, "", 10)
        for badge in badge_lines:
            pdf.multi_cell(0, 5, pdf_safe(badge))
        pdf.set_text_color(0, 0, 0)

    # Add separator
    pdf.ln(3)

    left_x = pdf.l_margin
    left_width = 110
    gap = 8
    right_x = left_x + left_width + gap
    right_width = pdf.w - pdf.r_margin - right_x
    start_y = pdf.get_y()

    pdf.set_xy(left_x, start_y)

    def write_heading(title: str):
        pdf.set_font(font_family, "B", 12)
        pdf.multi_cell(left_width, 7, pdf_safe(title))
        pdf.set_font(font_family, "", 10)

    def write_metric(label: str, value_key: str):
        value = info.get(value_key, "N/A")
        pdf.multi_cell(left_width, 6, pdf_safe(f"{label}: {value}"), align="L")

    write_heading("Price snapshot")
    write_metric("Share price", "currentPriceFormatted")
    write_metric("52-week high", "fiftyTwoWeekHighFormatted")
    write_metric("52-week low", "fiftyTwoWeekLowFormatted")

    slider = info.get("slider")
    if slider:
        low_label = slider.get("low_formatted", "N/A")
        high_label = slider.get("high_formatted", "N/A")
        price_label = slider.get("price_formatted", "N/A")
        try:
            pos = float(slider.get("position", 0.5))
        except Exception:
            pos = 0.5
        pos = max(0.0, min(1.0, pos))

        pdf.ln(1)
        pdf.set_font(font_family, "", 9)
        pdf.set_x(left_x)
        pdf.multi_cell(left_width, 5, pdf_safe(f"52-week range: {low_label} — {high_label}"))
        bar_x = left_x
        bar_y = pdf.get_y() + 1
        bar_height = 4
        bar_width = left_width
        pdf.set_draw_color(220, 220, 220)
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(bar_x, bar_y, bar_width, bar_height, "F")
        pointer_x = bar_x + bar_width * pos
        pdf.set_fill_color(44, 123, 229)
        pdf.rect(pointer_x - 1.5, bar_y - 1, 3, bar_height + 2, "F")
        pdf.set_y(bar_y + bar_height + 3)
        pdf.set_font(font_family, "", 9)
        pdf.multi_cell(left_width, 5, pdf_safe(f"Current price: {price_label}"))
        pdf.set_draw_color(0, 0, 0)

    history_points = info.get("history_points")
    if history_points and isinstance(history_points, (list, tuple)) and len(history_points) > 1:
        pdf.ln(3)
        pdf.set_font(font_family, "B", 11)
        pdf.multi_cell(left_width, 6, pdf_safe("Historical Market Price – Past 1 Year"))
        chart_x = left_x
        chart_y = pdf.get_y() + 1
        chart_height = 40
        chart_width = left_width
        pdf.set_draw_color(220, 220, 220)
        pdf.rect(chart_x, chart_y, chart_width, chart_height)
        try:
            values = [float(v) for v in history_points]
        except Exception:
            values = []
        if values:
            min_val = min(values)
            max_val = max(values)
            span = max(max_val - min_val, 1e-6)
            step = chart_width / max(1, len(values) - 1)
            prev_x = chart_x
            prev_y = chart_y + chart_height - ((values[0] - min_val) / span) * chart_height
            pdf.set_draw_color(44, 123, 229)
            for idx in range(1, len(values)):
                value = values[idx]
                x = chart_x + step * idx
                y = chart_y + chart_height - ((value - min_val) / span) * chart_height
                pdf.line(prev_x, prev_y, x, y)
                prev_x, prev_y = x, y
            pdf.set_draw_color(0, 0, 0)
        pdf.set_y(chart_y + chart_height + 4)

    pdf.ln(3)
    write_heading("Market behavior")
    write_metric("Beta", "betaFormatted")
    write_metric("52-week change", "fiftyTwoWeekChangeFormatted")
    write_metric("Volume", "volumeFormatted")

    pdf.ln(3)
    write_heading("Fundamentals snapshot")
    pdf.set_font(font_family, "B", 11)
    pdf.multi_cell(left_width, 6, pdf_safe("Valuation metrics"))
    pdf.set_font(font_family, "", 10)
    for label, key in [
        ("P/E ratio", "peFormatted"),
        ("EPS", "epsFormatted"),
        ("PEG ratio", "pegFormatted"),
        ("Dividend yield", "dividendYieldFormatted"),
        ("Market cap", "marketCapFormatted"),
    ]:
        write_metric(label, key)

    pdf.ln(2)
    pdf.set_font(font_family, "B", 11)
    pdf.multi_cell(left_width, 6, pdf_safe("Business quality metrics"))
    pdf.set_font(font_family, "", 10)
    for label, key in [
        ("Revenue", "revenueFormatted"),
        ("Revenue growth YoY", "revenueGrowthFormatted"),
        ("Operating margin", "operatingMarginFormatted"),
        ("Free cash flow", "fcfFormatted"),
        ("Debt to equity", "debtToEquityFormatted"),
    ]:
        write_metric(label, key)

    left_bottom = pdf.get_y()

    # Add AI insights
    def write_right_block(text: str, font_style=None, line_height=6):
        if font_style is None:
            font_style = (font_family, "", 10)
        font_family, font_weight, font_size = font_style
        pdf.set_font(font_family, font_weight, font_size)
        prev_margin = pdf.l_margin
        pdf.set_left_margin(right_x)
        pdf.set_x(right_x)
        pdf.multi_cell(right_width, line_height, pdf_safe(text), align="L")
        pdf.set_left_margin(prev_margin)

    pdf.set_xy(right_x, start_y)
    write_right_block(
        f"💡 AI-generated insights for {company}",
        font_style=(font_family, "B", 12),
        line_height=7,
    )
    cleaned_text = pdf_safe(insights_text.replace("•", "-").replace("**", ""))
    write_right_block(cleaned_text, font_style=(font_family, "", 10), line_height=6)

    right_bottom = pdf.get_y()
    pdf.set_y(max(left_bottom, right_bottom) + 4)

    pdf.set_font(font_family, "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0,
        5,
        pdf_safe("Stock Fundamentals Decoder App Made by Sharon Lin"),
        align="C",
    )
    pdf.ln(1)
    pdf.set_font(font_family, "", 8)
    pdf.multi_cell(
        0,
        4,
        pdf_safe(f"Disclaimer: {DISCLAIMER_TEXT}"),
        align="L",
    )
    pdf.set_text_color(0, 0, 0)

    out = pdf.output(dest="S")
    if isinstance(out, str):
        pdf_bytes = out.encode("latin-1", errors="ignore")
    else:
        pdf_bytes = out
    return pdf_bytes
