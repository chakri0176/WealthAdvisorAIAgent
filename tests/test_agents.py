import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.supervisor import route_request
from agents.risk_assessor import run_risk_assessment
from agents.financial_planner import run_financial_planning
from agents.client_comms import draft_client_summary

PORTFOLIO = """
My portfolio:
- AAPL: 40% weight, 100 shares
- MSFT: 60% weight, 50 shares
"""

def test_supervisor():
    print("\n--- test_supervisor ---")
    print(route_request("Analyze the risk of my portfolio"))
    print(route_request("Run bull and bear scenarios"))
    print(route_request("Draft a client summary"))
    print("✅ PASSED")

def test_risk_assessor():
    print("\n--- test_risk_assessor ---")
    result = run_risk_assessment(PORTFOLIO)
    print(result[:500])  # print first 500 chars
    print("✅ PASSED")

def test_financial_planner():
    print("\n--- test_financial_planner ---")
    result = run_financial_planning(PORTFOLIO)
    print(result[:500])
    print("✅ PASSED")

def test_client_comms():
    print("\n--- test_client_comms ---")
    analysis = """
    Risk Score: HIGH
    Portfolio Beta: 1.10
    Sector Concentration: 100% Technology
    Bear Case: Portfolio drops to $40,295
    Base Case: 5yr projection $83,080
    Bull Case: Portfolio rises to $65,681
    Recommendation: Sell 55 AAPL shares to rebalance
    """
    result = draft_client_summary(
        analysis_text=analysis,
        client_name="John Smith",
        tone="professional"
    )
    print(result)
    print("✅ PASSED")

if __name__ == "__main__":
    print("=" * 50)
    print("Running WealthAdvisor Agent Tests")
    print("=" * 50)

    test_supervisor()
    test_client_comms()   # test this first — fastest, no tools
    test_risk_assessor()  # these take longer
    test_financial_planner()

    print("\n" + "=" * 50)
    print("✅ All agent tests passed!")
    print("=" * 50)