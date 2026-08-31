import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.portfolio_tools import (
    get_stock_metrics,
    get_price_data,
    analyze_portfolio,
    search_bse_filings,
    index_bse_filing,
    get_financial_ratios,
)

def test_get_stock_metrics():
    print("\n--- test_get_stock_metrics ---")
    result = get_stock_metrics.invoke("TCS")
    print(result)
    print("✅ PASSED")

def test_get_price_data():
    print("\n--- test_get_price_data ---")
    result = get_price_data.invoke("TCS")
    print(result)
    print("✅ PASSED")

def test_analyze_portfolio():
    print("\n--- test_analyze_portfolio ---")
    holdings = '[{"ticker": "TCS", "weight": 0.4, "shares": 100}, {"ticker": "INFY", "weight": 0.6, "shares": 50}]'
    result = analyze_portfolio.invoke(holdings)
    print(result)
    print("✅ PASSED")

def test_index_bse_filing():
    print("\n--- test_index_bse_filing ---")
    result = index_bse_filing.invoke("TCS")
    print(result)
    print("✅ PASSED")

def test_search_bse_filings():
    print("\n--- test_search_bse_filings ---")
    result = search_bse_filings.invoke("What are TCS main risk factors?")
    print(result[:500])
    print("✅ PASSED")

def test_get_financial_ratios():
    print("\n--- test_get_financial_ratios ---")
    result = get_financial_ratios.invoke("TCS")
    print(result)
    print("✅ PASSED")

from agents.supervisor import route_request

def test_supervisor():
    print("\n--- test_supervisor ---")
    print(route_request("Analyze the risk of my portfolio with TCS and INFY"))
    print(route_request("Run a bull and bear scenario for my portfolio"))
    print(route_request("Draft a client summary for Rahul Sharma"))
    print("✅ PASSED")

from agents.risk_assessor import run_risk_assessment

def test_risk_assessor():
    print("\n--- test_risk_assessor ---")
    portfolio = """
    My Indian stock portfolio:
    - TCS: 40% weight, 100 shares at ₹2,317
    - INFY: 60% weight, 50 shares at ₹1,876
    Total value approximately ₹3,25,500
    """
    result = run_risk_assessment(portfolio)
    print(result)
    print("✅ PASSED")

from agents.financial_planner import run_financial_planning

def test_financial_planner():
    print("\n--- test_financial_planner ---")
    request = """
    Run a scenario analysis for this Indian stock portfolio:
    - TCS: 40% weight, 100 shares at ₹2,317
    - INFY: 60% weight, 50 shares at ₹1,876
    Total portfolio value: approximately ₹3,25,500
    """
    result = run_financial_planning(request)
    print(result)
    print("✅ PASSED")

if __name__ == "__main__":
    print("=" * 50)
    print("Running WealthAdvisor Tools Tests (Indian Stocks)")
    print("=" * 50)

    test_get_stock_metrics()
    test_get_price_data()
    test_analyze_portfolio()
    test_index_bse_filing()
    test_search_bse_filings()
    test_get_financial_ratios()
    test_supervisor()
    test_risk_assessor()
    test_financial_planner()

    print("\n" + "=" * 50)
    print("✅ All tools tests passed!")
    print("=" * 50)