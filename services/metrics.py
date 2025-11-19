"""Centralized definitions for each displayed metric and explanation helper."""

METRICS = {
    "share_price": {
        "name": "Share price",
        "meaning": "The current price at which the stock is trading.",
        "interpretation": (
            "Share price alone doesn’t tell you if a stock is expensive or cheap. "
            "It’s most useful when paired with valuation metrics like P/E, PEG, and "
            "the company’s earnings and cash flow."
        ),
    },
    "52_week_high": {
        "name": "52-week high",
        "meaning": "The highest price at which the stock traded in the past 52 weeks.",
        "interpretation": (
            "If today’s price is very close to the 52-week high, the stock has recently been strong and "
            "sentiment is optimistic. If it’s far below the high, the stock has pulled back and investors "
            "may have cooled on the story."
        ),
    },
    "52_week_low": {
        "name": "52-week low",
        "meaning": "The lowest price at which the stock traded in the past 52 weeks.",
        "interpretation": (
            "If today’s price is near the 52-week low, investors have been cautious or negative. "
            "If it’s well above the low, the stock has recovered from earlier weakness. "
            "Large gaps between low and current price often signal a big change in sentiment."
        ),
    },
    "beta": {
        "name": "Beta (vs market)",
        "meaning": "A measure of how much the stock’s price tends to move relative to the overall market.",
        "interpretation": (
            "For many broad indexes, beta ≈ 1.0 means the stock tends to move in line with the market. "
            "Beta below ~0.8 often feels calmer and more defensive; beta between ~0.8 and 1.2 feels roughly "
            "market-like; beta above ~1.5 is typically quite volatile. If you dislike big swings, lower-beta "
            "stocks may feel more comfortable; if you can tolerate swings, higher-beta stocks may be acceptable."
        ),
    },
    "52_week_change": {
        "name": "52-week change",
        "meaning": "The percentage change in the stock price over the past 52 weeks.",
        "interpretation": (
            "A positive value means the stock is up over the last year; a negative value means it’s down. "
            "Moves of ±10–20% are fairly normal; very large moves (for example ±50% or more) often reflect "
            "major changes in expectations, news, or sentiment and are worth understanding in more detail."
        ),
    },
    "volume": {
        "name": "Volume (latest)",
        "meaning": "The number of shares traded during the latest trading session.",
        "interpretation": (
            "High volume relative to the stock’s normal trading days suggests lots of interest or a reaction "
            "to news. Very low volume can mean fewer active buyers and sellers, which may make it harder to "
            "enter or exit large positions without moving the price."
        ),
    },
    "pe_ratio": {
        "name": "P/E Ratio",
        "meaning": "Price-to-Earnings ratio, showing how much investors pay for $1 of earnings.",
        "interpretation": (
            "A higher P/E usually means investors expect stronger growth or view the company as high quality. "
            "A lower P/E can mean slower expected growth or that the stock is out of favor. As a rough guide, "
            "single-digit P/Es often signal low expectations, 15–25 is common for many mature companies, and "
            "30+ is more typical of growth stories—but always compare to peers and the company’s own history."
        ),
    },
    "eps": {
        "name": "Earnings per share (EPS)",
        "meaning": "Earnings per Share: the company’s profit allocated to each share.",
        "interpretation": (
            "Positive and growing EPS generally points to a profitable, strengthening business. "
            "Falling EPS or consistently negative EPS can signal pressure on the business model, heavy "
            "investment, or early-stage development, all of which warrant a closer look."
        ),
    },
    "peg_ratio": {
        "name": "PEG Ratio",
        "meaning": "Price/Earnings to Growth ratio, which adjusts the P/E for expected earnings growth.",
        "interpretation": (
            "A PEG around 1.0 is often viewed as ‘roughly in line’ with the company’s growth. "
            "PEG below 1.0 can suggest that expected growth is high relative to the current P/E, while "
            "PEG clearly above 1.5–2.0 can indicate that the price is rich relative to expected growth. "
            "Always compare to the company’s own history and peers."
        ),
    },
    "dividend_yield": {
        "name": "Dividend yield",
        "meaning": "Annual dividend divided by share price, expressed as a percentage.",
        "interpretation": (
            "Dividend yield tells you how much cash return you get per dollar invested if the dividend stays flat. "
            "High yields (for example 4%+) can be attractive but sometimes indicate investor concern about dividend "
            "safety; very low yields may suggest the company reinvests cash for growth instead of paying shareholders."
        ),
    },
    "market_cap": {
        "name": "Market cap",
        "meaning": "Total value of all outstanding shares.",
        "interpretation": (
            "Mega-cap companies (hundreds of billions) are typically mature with diversified operations, while "
            "small- and mid-cap firms can grow faster but may face more volatility. Market cap helps frame the "
            "company’s scale versus peers."
        ),
    },
    "revenue": {
        "name": "Revenue (latest)",
        "meaning": "Total revenue from the most recent fiscal year reported.",
        "interpretation": (
            "Absolute revenue shows the sales base the company is working with. Large revenue bases often imply "
            "diverse product lines, while smaller ones can scale faster but may be concentrated."
        ),
    },
    "revenue_growth_yoy": {
        "name": "Revenue growth YoY",
        "meaning": "Year-over-year percentage change in revenue.",
        "interpretation": (
            "Consistently positive revenue growth suggests the company is expanding its sales base. "
            "Low single-digit growth (for example 0–5%) may indicate a mature or slower-growing business; "
            "double-digit growth (10%+) often points to stronger expansion; negative growth means sales are "
            "shrinking and you’ll want to understand why."
        ),
    },
    "operating_margin": {
        "name": "Operating margin",
        "meaning": "Operating income divided by revenue, expressed as a percentage.",
        "interpretation": (
            "Operating margin shows how much profit the company keeps from its core operations. "
            "Higher margins mean strong pricing power or efficient costs; very low margins mean the business "
            "is more sensitive to shocks. Industry norms differ widely."
        ),
    },
    "free_cash_flow": {
        "name": "Free cash flow (FCF)",
        "meaning": "Cash generated after operating expenses and capital investments.",
        "interpretation": (
            "Positive and stable free cash flow gives a company flexibility to pay dividends, buy back shares, "
            "pay down debt, or reinvest in growth. Persistently negative free cash flow can mean heavy investment "
            "or that the core business isn’t yet self-funding."
        ),
    },
    "debt_to_equity": {
        "name": "Debt / Equity",
        "meaning": "Ratio of total debt to shareholders’ equity.",
        "interpretation": (
            "Debt-to-equity shows how much the company leans on borrowing versus owner funding. "
            "Ratios below ~0.5 are often viewed as conservative, 0.5–1.0 as moderate, and well above 1.5–2.0 "
            "as heavily leveraged. Capital-intensive sectors naturally carry more debt, so compare to peers."
        ),
    },
}

# helper to get full explanation text for a given metric key. for use in tooltips, etc.
def explain(key: str) -> str:
    metric = METRICS[key]
    return (
        f"**What it means:**\n\n"
        f"{metric['meaning']}\n\n"
        f"**How to interpret:**\n\n"
        f"{metric['interpretation']}"
    )
