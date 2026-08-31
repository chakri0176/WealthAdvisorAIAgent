# tests/test_data_layer.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.market_data import get_key_metrics, get_price_history, calculate_portfolio_metrics
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
    result = get_key_metrics("TCS")
    print(result)
    assert "ticker" in result
    assert result["ticker"] == "TCS.NS"
    assert result["currency"] == "INR"
    print("✅ PASSED")

def test_get_price_history():
    print("\n--- test_get_price_history ---")
    df = get_price_history("TCS")
    print(df.tail(3))
    assert len(df) > 0
    print("✅ PASSED")

def test_calculate_portfolio_metrics():
    print("\n--- test_calculate_portfolio_metrics ---")
    holdings = [
        {"ticker": "TCS", "weight": 0.4, "shares": 100},
        {"ticker": "INFY", "weight": 0.35, "shares": 50},
        {"ticker": "RELIANCE", "weight": 0.25, "shares": 30},
    ]
    result = calculate_portfolio_metrics(holdings)
    print("Positions:", result["num_positions"])
    for h in result["holdings"]:
        print(h["ticker"], "-", h["company_name"], "- Beta:", h["beta"])
    assert result["num_positions"] == 3
    print("✅ PASSED")

def test_multiple_indian_stocks():
    print("\n--- test_multiple_indian_stocks ---")
    tickers = ["HDFCBANK", "WIPRO", "BAJFINANCE", "ITC", "TATAMOTORS"]
    for ticker in tickers:
        result = get_key_metrics(ticker)
        print(f"{result['ticker']} - {result['company_name']} - ₹{result['current_price']}")
        assert result["ticker"].endswith(".NS")
        assert result["currency"] == "INR"
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

    # Use sample Indian company text instead of SEC filing
    sample_text = """
    Tata Consultancy Services Limited (TCS) Annual Report 2025.
    TCS is India's largest IT services company by market capitalization.
    
    Risk Factors:
    The company faces risks from client concentration, with top 10 clients
    contributing approximately 35% of revenue. Currency fluctuation risk
    is significant as majority of revenue comes from exports in USD and EUR.
    
    Regulatory risks include compliance with data protection laws across
    multiple jurisdictions including GDPR in Europe and proposed PDPB in India.
    
    Competition from global IT firms such as Infosys, Wipro, HCL Technologies
    and international players like Accenture and IBM poses ongoing challenges.
    
    The company's revenue grew 8.2% year-on-year to reach ₹2,40,893 crore
    in FY2025. Net profit margin remained stable at 19.1%.
    
    Key risks for investors include:
    1. Global economic slowdown affecting IT spending
    2. Talent acquisition and retention challenges
    3. Cybersecurity and data breach risks
    4. Geopolitical risks affecting global operations
    5. Technology disruption from AI and automation
    """ * 10  # repeat to get enough content to chunk

    # Index it
    chunks = index_document(
        text=sample_text,
        doc_id="TCS_Annual_2025",
        metadata={
            "ticker": "TCS.NS",
            "form_type": "Annual Report",
            "filing_date": "2025-03-31"
        }
    )
    print("Chunks indexed:", chunks)
    assert chunks > 0

    # Query it
    results = query("What are the main risk factors for TCS?")
    print("Results found:", len(results))
    print("Top result preview:", results[0]["text"][:300])
    assert len(results) > 0
    print("✅ PASSED")

# ── Run all tests ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Running WealthAdvisor Data Layer Tests (Indian Stocks)")
    print("=" * 50)

    test_get_key_metrics()
    test_get_price_history()
    test_calculate_portfolio_metrics()
    test_multiple_indian_stocks()
    test_chunk_text()
    test_index_and_query()

    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)