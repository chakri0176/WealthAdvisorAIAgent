from langchain_core.tools import tool
from data.market_data import get_key_metrics, get_price_history, calculate_portfolio_metrics
from data.bse_fetcher import get_annual_report_text, fetch_financial_ratios
from data.vector_store import index_document, query
import json


@tool
def get_stock_metrics(ticker: str) -> str:
    """
    Get key financial metrics for an Indian NSE listed stock.
    Returns beta, market cap, current price in INR, sector and more.
    Input is NSE ticker like: 'TCS', 'INFY', 'RELIANCE'
    """
    return json.dumps(get_key_metrics(ticker))


@tool
def get_price_data(ticker: str) -> str:
    """
    Get 1-year historical price data for an Indian NSE stock.
    Returns start price, end price, 1yr return, high, low in INR.
    Input is NSE ticker like: 'TCS', 'INFY', 'RELIANCE'
    """
    price_history = get_price_history(ticker, period="1y")
    summary = {
        "ticker": ticker,
        "currency": "INR",
        "start_price": round(float(price_history["Close"].iloc[0]), 2),
        "end_price": round(float(price_history["Close"].iloc[-1]), 2),
        "return_1y": round(float(price_history["Close"].iloc[-1] / price_history["Close"].iloc[0] - 1) * 100, 2),
        "max_price": round(float(price_history["Close"].max()), 2),
        "min_price": round(float(price_history["Close"].min()), 2),
    }
    return json.dumps(summary)


@tool
def analyze_portfolio(holdings_json: str) -> str:
    """
    Analyze an Indian stock portfolio given a JSON list of holdings.
    Input must be a JSON string like:
    '[{"ticker": "TCS", "weight": 0.4, "shares": 100}]'
    Returns portfolio metrics for each holding and total positions.
    Tickers should be NSE symbols like TCS, INFY, RELIANCE.
    """
    holdings = json.loads(holdings_json)
    return json.dumps(calculate_portfolio_metrics(holdings))


@tool
def index_bse_filing(ticker: str) -> str:
    """
    Download and index the latest annual report for an Indian NSE listed company.
    Call this before searching filings for a company.
    Input is NSE ticker like: 'TCS', 'INFY', 'RELIANCE'
    Returns confirmation of how many chunks were indexed.
    Skips automatically if already indexed.
    """
    from data.vector_store import get_collection

    collection = get_collection()

    # Skip if already indexed
    existing = collection.get(where={"ticker": f"{ticker}.NS"})
    if existing and len(existing["ids"]) > 0:
        return f"Filing for {ticker} already indexed ({len(existing['ids'])} chunks) — skipping."

    text = get_annual_report_text(ticker)
    if not text or len(text) < 100:
        return f"Could not fetch annual report for {ticker}"

    chunks = index_document(
        text=text,
        doc_id=f"{ticker}_Annual_2025",
        metadata={
            "ticker": f"{ticker}.NS",
            "form_type": "Annual Report",
            "filing_date": "2025-03-31"
        }
    )
    return f"Indexed {chunks} chunks for {ticker} Annual Report"


@tool
def search_bse_filings(query_text: str) -> str:
    """
    Search through indexed BSE annual reports to find relevant information.
    Use this to find risk factors, business description, financial highlights.
    Input is a natural language question like: 'What are TCS risk factors?'
    """
    results = query(query_text, n_results=5)

    if not results:
        return "No relevant filing content found."

    output = []
    for i, result in enumerate(results):
        ticker = result["metadata"].get("ticker", "?")
        form_type = result["metadata"].get("form_type", "?")
        filing_date = result["metadata"].get("filing_date", "?")
        text_preview = result["text"][:500]
        output.append(
            f"[Result {i+1}] {ticker} | {form_type} | {filing_date}\n{text_preview}"
        )

    return "\n\n---\n\n".join(output)


@tool
def get_financial_ratios(ticker: str) -> str:
    """
    Get key financial ratios for an Indian NSE listed stock.
    Returns PE ratio, PB ratio, ROE, debt-to-equity, profit margins, EPS.
    Input is NSE ticker like: 'TCS', 'INFY', 'RELIANCE'
    """
    ratios = fetch_financial_ratios(ticker)
    return json.dumps(ratios, indent=2)