# tests/test_data_layer.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.market_data import get_key_metrics, get_price_history, calculate_portfolio_metrics
from data.sec_fetcher import get_cik, get_recent_filings, fetch_filing_text
from data.vector_store import chunk_text, index_document, query
from config.settings import get_settings
from dotenv import load_dotenv
load_dotenv()

settings = get_settings()

os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
os.environ["GEMINI_MODEL"] = settings.gemini_model

# ── market_data tests ─────────────────────────────────────────────────────────

def test_get_key_metrics():
    print("\n--- test_get_key_metrics ---")
    result = get_key_metrics("AAPL")
    print(result)
    assert "ticker" in result
    assert result["ticker"] == "AAPL"
    print("✅ PASSED")

def test_get_price_history():
    print("\n--- test_get_price_history ---")
    df = get_price_history("AAPL")
    print(df.tail(3))
    assert len(df) > 0
    print("✅ PASSED")

def test_calculate_portfolio_metrics():
    print("\n--- test_calculate_portfolio_metrics ---")
    holdings = [
        {"ticker": "AAPL", "weight": 0.4, "shares": 100},
        {"ticker": "MSFT", "weight": 0.35, "shares": 50},
        {"ticker": "GOOGL", "weight": 0.25, "shares": 30},
    ]
    result = calculate_portfolio_metrics(holdings)
    print("Positions:", result["num_positions"])
    for h in result["holdings"]:
        print(h["ticker"], "-", h["company_name"], "- Beta:", h["beta"])
    assert result["num_positions"] == 3
    print("✅ PASSED")

# ── sec_fetcher tests ─────────────────────────────────────────────────────────

def test_get_cik():
    print("\n--- test_get_cik ---")
    cik = get_cik("AAPL")
    print("CIK:", cik)
    assert cik == "0000320193"
    print("✅ PASSED")

def test_get_recent_filings():
    print("\n--- test_get_recent_filings ---")
    filings = get_recent_filings("AAPL")
    print("Filings found:", len(filings))
    for f in filings:
        print(f["form"], "-", f["filingDate"])
    assert len(filings) > 0
    print("✅ PASSED")

def test_fetch_filing_text():
    print("\n--- test_fetch_filing_text ---")
    filings = get_recent_filings("AAPL")
    text = fetch_filing_text(filings[0]["accessionNumber"], "AAPL")
    print("Characters fetched:", len(text))
    print("Preview:", text[:200])
    assert len(text) > 0
    print("✅ PASSED")

# ── vector_store tests ────────────────────────────────────────────────────────

def test_chunk_text():
    print("\n--- test_chunk_text ---")
    text = "a" * 5000
    chunks = chunk_text(text)
    print("Total chunks:", len(chunks))
    print("Chunk size:", len(chunks[0]))
    assert len(chunks) > 0
    assert len(chunks[0]) == 1000
    print("✅ PASSED")

def test_index_and_query():
    print("\n--- test_index_and_query ---")
    # Fetch filing
    filings = get_recent_filings("AAPL")
    text = fetch_filing_text(filings[0]["accessionNumber"], "AAPL")

    # Index it
    chunks = index_document(
        text=text,
        doc_id="AAPL_10K_2025",
        metadata={
            "ticker": "AAPL",
            "form_type": "10-K",
            "filing_date": filings[0]["filingDate"]
        }
    )
    print("Chunks indexed:", chunks)
    assert chunks > 0

    # Query it
    results = query("What are the main risk factors for Apple?")
    print("Results found:", len(results))
    print("Top result preview:", results[0]["text"][:300])
    assert len(results) > 0
    print("✅ PASSED")


# ── Run all tests ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Running WealthAdvisor Data Layer Tests")
    print("=" * 50)

    test_get_key_metrics()
    test_get_price_history()
    test_calculate_portfolio_metrics()
    test_get_cik()
    test_get_recent_filings()
    test_fetch_filing_text()
    test_chunk_text()
    test_index_and_query()

    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)