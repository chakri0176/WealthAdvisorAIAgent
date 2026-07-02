import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from clients.client_memory import (
    save_client_profile,
    save_analysis_session,
    load_client_history,
    get_client_profile
)

def test_save_client_profile():
    print("\n--- test_save_client_profile ---")
    save_client_profile(
        client_id="client_001",
        client_name="John Smith",
        risk_tolerance="moderate",
        investment_goals="Retirement in 10 years",
        time_horizon="10 years"
    )
    print("✅ PASSED")

def test_get_client_profile():
    print("\n--- test_get_client_profile ---")
    profile = get_client_profile("client_001")
    print("Profile:", profile)
    assert profile is not None
    assert profile["client_name"] == "John Smith"
    assert profile["risk_tolerance"] == "moderate"
    print("✅ PASSED")

def test_save_analysis_session():
    print("\n--- test_save_analysis_session ---")
    save_analysis_session(
        client_id="client_001",
        session_id=str(uuid.uuid4()),
        portfolio_data="AAPL 40%, MSFT 35%, GOOGL 25%",
        risk_output="Portfolio beta 1.096, sector concentration 75% tech",
        planning_output="Bear: $40K, Base: $83K, Bull: $65K",
        client_summary="Dear John, your portfolio carries MODERATE risk...",
        risk_score="MODERATE"
    )
    print("✅ PASSED")

def test_load_client_history():
    print("\n--- test_load_client_history ---")
    history = load_client_history("client_001")
    print("Sessions found:", len(history))
    print("Latest session:", history[0]["created_at"])
    print("Risk score:", history[0]["risk_score"])
    assert len(history) > 0
    assert history[0]["risk_score"] == "MODERATE"
    print("✅ PASSED")

def test_client_not_found():
    print("\n--- test_client_not_found ---")
    profile = get_client_profile("nonexistent_client")
    assert profile is None
    print("✅ PASSED — returns None for unknown client")

def test_multiple_sessions():
    print("\n--- test_multiple_sessions ---")
    # Use test client, not real client
    for i in range(3):
        save_analysis_session(
            client_id="test_client_999",  # ← different ID
            session_id=str(uuid.uuid4()),
            portfolio_data=f"Session {i+1} portfolio",
            risk_score=["LOW", "MODERATE", "HIGH"][i]
        )
    history = load_client_history("test_client_999", limit=3)
    print("Last 3 sessions:")
    for h in history:
        print(f"  - {h['created_at']} | Risk: {h['risk_score']}")
    assert len(history) == 3
    print("✅ PASSED")

def test_api_memory_integration():
    print("\n--- test_api_memory_integration ---")
    from clients.client_memory import load_client_history, get_client_profile
    
    # Check John Smith's profile
    profile = get_client_profile("client_001")
    print("Profile:", profile)
    
    # Check saved sessions
    history = load_client_history("client_001")
    print("Sessions found:", len(history))
    for h in history:
        print(f"  - {h['created_at']} | Risk: {h['risk_score']}")
    
    print("✅ PASSED")

def test_real_api_sessions():
    print("\n--- test_real_api_sessions ---")
    from clients.client_memory import load_client_history
    
    history = load_client_history("client_001", limit=10)
    print(f"Total sessions: {len(history)}")
    for h in history:
        print(f"  Date: {h['created_at'][:19]}")
        print(f"  Risk: {h['risk_score']}")
        print(f"  Has real risk output: {len(h['risk_output']) > 100}")
        print(f"  Portfolio: {h['portfolio_data'][:50]}")
        print()
    print("✅ PASSED")

if __name__ == "__main__":
    print("=" * 50)
    print("Running Client Memory Tests")
    print("=" * 50)

    test_save_client_profile()
    test_get_client_profile()
    test_save_analysis_session()
    test_load_client_history()
    test_client_not_found()
    test_multiple_sessions()
    test_api_memory_integration()
    test_real_api_sessions()
    
    print("\n" + "=" * 50)
    print("✅ All client memory tests passed!")
    print("=" * 50)