from langchain_core.tools import tool
from data.market_data import get_key_metrics, get_price_history, calculate_portfolio_metrics
from data.sec_fetcher import get_recent_filings, fetch_filing_text
from data.vector_store import get_embeddings,get_collection,index_document,query
import json

@tool
def get_stock_metrics(ticker: str)->str:
    """
    Get key financial metrics for a single stock ticker.
    Returns PE ratio, beta, market cap, 52-week range, and more.
    """
    return json.dumps(get_key_metrics(ticker))

@tool
def get_price_data(ticker: str)->str:
    """
    Get 1-year historical price data for a ticker.
    Returns start price, end price, 1yr return, high, low and avg volume.
    """
    price_history = get_price_history(ticker,period="1y")
    summary = {
        "ticker":ticker,
        "start_price": round(float(price_history["Close"].iloc[0]),2),
        "end_price": round(float(price_history["Close"].iloc[-1]),2),
        "return_1y": round(float(price_history["Close"].iloc[-1] / price_history["Close"].iloc[0] - 1) * 100, 2),
        "max_price": round(float(price_history["Close"].max()),2),
        "min_price": round(float(price_history["Close"].min()),2)
    }
    return json.dumps(summary)

@tool
def analyze_portfolio(holdings_json: str)->str:
    """
    Analyze a portfolio's metrics given a JSON list of holdings.
    Input must be a JSON string like: '[{"ticker": "AAPL", "weight": 0.4, "shares": 100}]'
    Returns portfolio metrics for each holding and total positions.
    """
    holdings = json.loads(holdings_json)
    return json.dumps(calculate_portfolio_metrics(holdings))

@tool
def search_sec_filings(query_text: str)->str:
    """
    Search through indexed SEC filings to find relevant information.
    Use this to find risk factors, financial data, or any information from company filings.
    Input is a natural language question like: 'What are Apple's main risk factors?'
    """
    results = query(query_text,n_results=5)
    if not results:
        return "No relevant SEC filing content found."
    output = []
    for i, result in enumerate(results):
        ticker = result["metadata"].get("ticker","?")
        form_type = result["metadata"].get("form_type","?")
        filing_date = result["metadata"].get("filing_date","?")
        text_preview = result["text"][:500]
        
        output.append(f"[Result {i+1}] {ticker} | {form_type} | {filing_date}\n{text_preview}")
    return "\n\n---\n\n".join(output)

@tool
def index_sec_filing(ticker: str) -> str:
    """
    Download and index the latest 10-K SEC filing for a given ticker.
    Call this before searching SEC filings for a company.
    """
    from data.vector_store import get_collection
    collection = get_collection()
    
    # Check if already indexed
    existing = collection.get(where={"ticker": ticker})
    if existing and len(existing["ids"]) > 0:
        return f"Filing for {ticker} already indexed ({len(existing['ids'])} chunks) — skipping download."
    
    filings = get_recent_filings(ticker, form_type="10-K", count=1)
    if not filings:
        return f"No filings found for {ticker}"
    filing = filings[0]
    text = fetch_filing_text(filing["accessionNumber"], ticker)
    chunks = index_document(
        text=text,
        doc_id=f"{ticker}_10K_{filing['filingDate']}",
        metadata={
            "ticker": ticker,
            "form_type": "10-K",
            "filing_date": filing["filingDate"]
        }
    )
    return f"Indexed {chunks} chunks for {ticker} 10-K filed on {filing['filingDate']}"