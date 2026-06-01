import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.portfolio_tools import (
    get_stock_metrics,
    get_price_data,
    analyze_portfolio,
    search_sec_filings,
    index_sec_filing,
)

def test_get_stock_metrics():
    print("\n--- test_get_stock_metrics ---")
    result = get_stock_metrics.invoke("AAPL")
    print(result)
    print("✅ PASSED")

def test_get_price_data():
    print("\n--- test_get_price_data ---")
    result = get_price_data.invoke("AAPL")
    print(result)
    print("✅ PASSED")

def test_analyze_portfolio():
    print("\n--- test_analyze_portfolio ---")
    holdings = '[{"ticker": "AAPL", "weight": 0.4, "shares": 100}, {"ticker": "MSFT", "weight": 0.6, "shares": 50}]'
    result = analyze_portfolio.invoke(holdings)
    print(result)
    print("✅ PASSED")

def test_index_sec_filing():
    print("\n--- test_index_sec_filing ---")
    result = index_sec_filing.invoke("AAPL")
    print(result)
    print("✅ PASSED")

def test_search_sec_filings():
    print("\n--- test_search_sec_filings ---")
    result = search_sec_filings.invoke("What are Apple's main risk factors?")
    print(result[:500])
    print("✅ PASSED")

if __name__ == "__main__":
    print("=" * 50)
    print("Running WealthAdvisor Tools Tests")
    print("=" * 50)

    test_get_stock_metrics()
    test_get_price_data()
    test_analyze_portfolio()
    test_index_sec_filing()
    test_search_sec_filings()

    print("\n" + "=" * 50)
    print("✅ All tools tests passed!")
    print("=" * 50)