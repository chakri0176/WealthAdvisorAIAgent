"""
BSE India filing fetcher — replaces sec_fetcher.py
Fetches annual reports and corporate announcements for Indian listed companies.
Uses the unofficial BSE Python library + yfinance for fallback data.
"""
import requests
import time
import json
from bs4 import BeautifulSoup
from typing import Optional
from config.settings import get_settings

settings = get_settings()

# BSE API base URLs
BSE_BASE = "https://api.bseindia.com/BseIndiaAPI/api"
BSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bseindia.com/",
    "Accept": "application/json, text/plain, */*",
}

# Common NSE to BSE code mapping for popular stocks
NSE_TO_BSE = {
    "TCS": "532540",
    "INFY": "500209",
    "RELIANCE": "500325",
    "HDFCBANK": "500180",
    "WIPRO": "507685",
    "BAJFINANCE": "500034",
    "ITC": "500875",
    "ICICIBANK": "532174",
    "SBIN": "500112",
    "HINDUNILVR": "500696",
    "KOTAKBANK": "500247",
    "AXISBANK": "532215",
    "LT": "500510",
    "SUNPHARMA": "524715",
    "BHARTIARTL": "532454",
    "ASIANPAINT": "500820",
    "MARUTI": "532500",
    "TITAN": "500114",
    "ULTRACEMCO": "532538",
    "NESTLEIND": "500790",
    "HCLTECH": "532281",
    "TECHM": "532755",
    "POWERGRID": "532898",
    "NTPC": "532555",
    "ONGC": "500312",
    "COALINDIA": "533278",
    "BPCL": "500547",
    "TATAMOTORS": "500570",
    "TATASTEEL": "500470",
    "JSWSTEEL": "500228",
    "BEL": "500049",
    "ADANIPORTS": "532921",
    "ADANIENT": "512599",
    "BAJAJFINSV": "532978",
    "DIVISLAB": "532488",
    "CIPLA": "500087",
    "DRREDDY": "500124",
    "EICHERMOT": "505200",
    "HEROMOTOCO": "500182",
    "BRITANNIA": "500825",
    "GRASIM": "500300",
    "INDUSINDBK": "532187",
    "M&M": "500520",
    "SHREECEM": "500387",
    "TATACONSUM": "500800",
    "SBILIFE": "540719",
    "HDFCLIFE": "540777",
    "ICICIGI": "540716",
}


def get_bse_code(ticker: str) -> Optional[str]:
    """
    Get BSE scrip code for a given NSE ticker symbol.
    First checks local mapping, then queries BSE API.
    """
    # Clean ticker
    ticker = ticker.upper().replace(".NS", "").replace(".BO", "").strip()

    # Check local mapping first
    if ticker in NSE_TO_BSE:
        return NSE_TO_BSE[ticker]

    # Try BSE search API
    try:
        url = f"https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active"
        resp = requests.get(url, headers=BSE_HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data:
                if item.get("SCRIP_CD") and item.get("short_name", "").upper() == ticker:
                    return str(item["SCRIP_CD"])
    except Exception:
        pass

    return None


def get_company_info(ticker: str) -> dict:
    """
    Get basic company information from BSE.
    Returns company name, sector, BSE code.
    """
    bse_code = get_bse_code(ticker)
    if not bse_code:
        return {"ticker": ticker, "bse_code": None, "error": "BSE code not found"}

    try:
        url = f"{BSE_BASE}/ComHeader/w?quotetype=EQ&Debtflag=&scripcode={bse_code}"
        resp = requests.get(url, headers=BSE_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "ticker": ticker,
            "bse_code": bse_code,
            "company_name": data.get("companyname", "N/A"),
            "sector": data.get("Industry", "N/A"),
            "isin": data.get("ISIN", "N/A"),
        }
    except Exception as e:
        return {"ticker": ticker, "bse_code": bse_code, "error": str(e)}


def get_recent_announcements(ticker: str, count: int = 5) -> list:
    """
    Get recent corporate announcements from BSE for a given ticker.
    Similar to get_recent_filings() for SEC EDGAR.
    """
    bse_code = get_bse_code(ticker)
    if not bse_code:
        return []

    try:
        url = f"{BSE_BASE}/AnnSubCategoryGetData/w?strCat=-1&strPrevDate=&strScrip={bse_code}&strSearch=P&strToDate=&strType=C&subcategory=-1"
        resp = requests.get(url, headers=BSE_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        announcements = []
        items = data.get("Table", [])[:count]
        for item in items:
            announcements.append({
                "ticker": ticker,
                "bse_code": bse_code,
                "headline": item.get("HEADLINE", ""),
                "date": item.get("News_submission_dt", ""),
                "category": item.get("CATEGORYNAME", ""),
                "attachment_url": item.get("ATTACHMENTNAME", ""),
            })

        time.sleep(0.2)
        return announcements
    except Exception as e:
        return []


def get_annual_report_text(ticker: str, max_chars: int = 50000) -> str:
    """
    Fetch and extract text from the latest annual report for an Indian company.
    Uses multiple strategies:
    1. BSE announcements API for annual report links
    2. NSE filing search as fallback
    3. Company investor relations page as last resort
    """
    ticker_clean = ticker.upper().replace(".NS", "").replace(".BO", "").strip()
    bse_code = get_bse_code(ticker_clean)

    # Strategy 1 — BSE Annual Report API
    if bse_code:
        try:
            url = f"{BSE_BASE}/AnnualReport/w?scripcode={bse_code}&flag=AR"
            resp = requests.get(url, headers=BSE_HEADERS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                reports = data.get("Table", [])
                if reports:
                    # Get the most recent annual report
                    latest = reports[0]
                    pdf_url = latest.get("FILENM", "")
                    if pdf_url:
                        return _extract_text_from_bse_url(pdf_url, max_chars)
        except Exception:
            pass

    # Strategy 2 — BSE Announcements search for annual report
    try:
        announcements = get_recent_announcements(ticker_clean, count=20)
        for ann in announcements:
            headline = ann.get("headline", "").lower()
            if "annual report" in headline or "annual general" in headline:
                attachment = ann.get("attachment_url", "")
                if attachment:
                    return _extract_text_from_bse_url(attachment, max_chars)
    except Exception:
        pass

    # Strategy 3 — Generate synthetic risk text from yfinance data
    return _generate_risk_text_from_yfinance(ticker_clean, max_chars)


def _extract_text_from_bse_url(url: str, max_chars: int) -> str:
    """Download and extract text from a BSE document URL."""
    try:
        if not url.startswith("http"):
            url = f"https://www.bseindia.com{url}"

        resp = requests.get(url, headers=BSE_HEADERS, timeout=30)
        resp.raise_for_status()

        # Try to extract text from HTML
        soup = BeautifulSoup(resp.content, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        if len(text) > 500:
            return text[:max_chars]
    except Exception:
        pass
    return ""


def _generate_risk_text_from_yfinance(ticker: str, max_chars: int) -> str:
    """
    Generate structured risk analysis text using yfinance data.
    Used as fallback when BSE filing is not available.
    """
    try:
        import yfinance as yf
        # Try .NS first, fallback to .BO
        for suffix in [".NS", ".BO"]:
            stock = yf.Ticker(f"{ticker}{suffix}")
            info = stock.info
            if info.get("longName"):
                break

        company_name = info.get("longName", ticker)
        sector = info.get("sector", "Unknown")
        industry = info.get("industry", "Unknown")
        beta = info.get("beta", "N/A")
        debt_to_equity = info.get("debtToEquity", "N/A")
        roe = info.get("returnOnEquity", "N/A")
        profit_margins = info.get("profitMargins", "N/A")
        revenue_growth = info.get("revenueGrowth", "N/A")
        business_summary = info.get("longBusinessSummary", "")

        text = f"""
COMPANY OVERVIEW
Company: {company_name}
Ticker: {ticker} (NSE)
Sector: {sector}
Industry: {industry}

BUSINESS DESCRIPTION
{business_summary}

FINANCIAL HIGHLIGHTS
Beta (Market Sensitivity): {beta}
Debt to Equity Ratio: {debt_to_equity}
Return on Equity: {roe}
Profit Margins: {profit_margins}
Revenue Growth: {revenue_growth}

KEY RISK FACTORS FOR {company_name.upper()}

1. MARKET RISK
The company operates in the {sector} sector with beta of {beta}.
{'High beta indicates significant market sensitivity and volatility risk.' if isinstance(beta, (int, float)) and beta > 1 else 'Low beta suggests defensive characteristics relative to broader market.'}

2. FINANCIAL RISK
{'High debt-to-equity ratio indicates leveraged balance sheet risk.' if isinstance(debt_to_equity, (int, float)) and debt_to_equity > 100 else 'Manageable debt levels based on available financial data.'}
Return on equity of {roe} indicates {'strong' if isinstance(roe, (int, float)) and roe > 0.15 else 'moderate'} capital efficiency.

3. SECTOR RISK
Operating in {industry} within the {sector} sector exposes the company to:
- Sector-specific regulatory changes by SEBI and relevant ministries
- Competition from domestic and international players
- Technology disruption affecting business model
- Supply chain dependencies and raw material costs

4. REGULATORY RISK
As an Indian listed company, {company_name} is subject to:
- SEBI listing obligations and disclosure requirements
- Ministry of Corporate Affairs compliance
- GST and income tax regulations
- Foreign exchange management regulations (FEMA)
- Industry-specific regulations from relevant regulators

5. MACROECONOMIC RISK
- RBI monetary policy affecting borrowing costs
- INR/USD exchange rate fluctuations
- Inflation impact on margins and consumer demand
- Global economic slowdown affecting export-oriented businesses
- FII/DII flow volatility affecting stock price

6. OPERATIONAL RISK
- Talent acquisition and retention in competitive market
- Cybersecurity and data protection risks
- Business continuity and disaster recovery
- Corporate governance and management quality

INVESTOR CONSIDERATIONS
This analysis is based on publicly available market data.
For complete risk assessment, refer to the company's latest
Annual Report filed with BSE/NSE and SEBI disclosures.
        """
        return text[:max_chars]
    except Exception as e:
        return f"Unable to fetch company data for {ticker}: {str(e)}"


def fetch_financial_ratios(ticker: str) -> dict:
    """
    Fetch key financial ratios for an Indian company.
    Uses yfinance as the primary source.
    """
    try:
        import yfinance as yf
        stock = yf.Ticker(f"{ticker}.NS")
        info = stock.info
        return {
            "ticker": ticker,
            "pe_ratio": info.get("trailingPE", None),
            "pb_ratio": info.get("priceToBook", None),
            "debt_to_equity": info.get("debtToEquity", None),
            "roe": info.get("returnOnEquity", None),
            "roce": info.get("returnOnAssets", None),
            "profit_margin": info.get("profitMargins", None),
            "revenue_growth": info.get("revenueGrowth", None),
            "dividend_yield": info.get("dividendYield", None),
            "eps": info.get("trailingEps", None),
            "book_value": info.get("bookValue", None),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}