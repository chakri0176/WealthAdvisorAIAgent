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

from agents.supervisor import route_request

def test_supervisor():
    print("\n--- test_supervisor ---")
    print(route_request("Analyze the risk of my portfolio with AAPL and MSFT"))
    print(route_request("Run a bull and bear scenario for my portfolio"))
    print(route_request("Draft a client summary for John Smith"))
    print("✅ PASSED")
    
from agents.risk_assessor import run_risk_assessment

def test_risk_assessor():
    print("\n--- test_risk_assessor ---")
    portfolio = """
    My portfolio:
    - AAPL: 40% weight, 100 shares
    - MSFT: 60% weight, 50 shares
    """
    result = run_risk_assessment(portfolio)
    print(result)
    print("✅ PASSED")

from agents.financial_planner import run_financial_planning

def test_financial_planner():
    print("\n--- test_financial_planner ---")
    request = """
    Run a scenario analysis for this portfolio:
    - AAPL: 40% weight, 100 shares
    - MSFT: 60% weight, 50 shares
    Total portfolio value: approximately $51,734
    """
    result = run_financial_planning(request)
    print(result)
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
    test_supervisor()
    test_risk_assessor()
    test_financial_planner()
    
    print("\n" + "=" * 50)
    print("✅ All tools tests passed!")
    print("=" * 50)
    

    
