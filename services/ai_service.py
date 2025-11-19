"""OpenAI chat helper for generating fundamentals insights."""
import os
from typing import Optional

from openai import OpenAI


def _build_prompt(
    company: str,
    ticker: str,
    industry: str,
    company_summary: str,
    revenue: str,
    revenue_growth: str,
    operating_margin: str,
    free_cash_flow: str,
    debt_to_equity: str,
    pe: str,
    eps: Optional[str],
    peg: Optional[str],
    market_cap: str,
    dividend_yield: str,
    beta: str,
) -> str:
    return """You are a patient financial educator helping a 25–35 year old index fund investor
understand {company} ({ticker}). They are NOT trying to time the market or day-trade — they just
want to learn the business fundamentals.

{company} operates in the {industry} industry.
Here is how the company currently describes its products, focus, or priorities:
{company_summary}

Business fundamentals:
- Revenue (latest FY): {rev}
- Revenue growth YoY: {rev_growth}
- Operating margin: {op_margin}
- Free cash flow (FCF): {fcf}
- Debt-to-equity: {dte}

Valuation snapshot:
- P/E ratio: {pe}
- Earnings per share (EPS): {eps}
- PEG ratio: {peg}
- Market cap: {market_cap}
- Dividend yield: {dividend_yield}

Market behavior:
- Beta (volatility vs market): {beta}

Task:
1. Respond with 5-6 bullet points. Each bullet should lead with a short bolded keyword or phrase
   (e.g., **Healthy and resilient business**) followed by 1–3 sentences of explanation.
2. Cover the business fundamentals first (growth, margins, FCF, leverage), then tie in valuation context, and, if helpful, briefly note what beta says about how bumpy the ride might feel versus a broad index (without calling it good or bad).
3. Explicitly connect each insight back to the company’s current products/focus/priorities described above (e.g., how a margin trend links to a product line).
4. End with one bullet that gives a friendly heads-up about what an index-fund-first investor might watch over
   the next few years.
5. Avoid buy/sell language. Keep everything under 250 words and make the tone friendly and non-jargony.
""".format(
        company=company,
        ticker=ticker.upper(),
        industry=industry,
        company_summary=company_summary,
        rev=revenue,
        rev_growth=revenue_growth,
        op_margin=operating_margin,
        fcf=free_cash_flow,
        dte=debt_to_equity,
        pe=pe,
        eps=eps,
        peg=peg,
        market_cap=market_cap,
        dividend_yield=dividend_yield,
        beta=beta,
    )


def generate_company_insights(
    *,
    company: str,
    ticker: str,
    industry: str,
    company_summary: str,
    revenue: str,
    revenue_growth: str,
    operating_margin: str,
    free_cash_flow: str,
    debt_to_equity: str,
    pe: str,
    eps: str,
    peg: str,
    market_cap: str,
    dividend_yield: str,
    beta: str,
    model: str = "gpt-5-mini",
) -> str:
    """Call the OpenAI Chat Completions API and return the generated insights."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    prompt = _build_prompt(
        company=company,
        ticker=ticker,
        industry=industry,
        company_summary=company_summary,
        revenue=revenue,
        revenue_growth=revenue_growth,
        operating_margin=operating_margin,
        free_cash_flow=free_cash_flow,
        debt_to_equity=debt_to_equity,
        pe=pe,
        eps=eps,
        peg=peg,
        market_cap=market_cap,
        dividend_yield=dividend_yield,
        beta=beta,
    )
    response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content
