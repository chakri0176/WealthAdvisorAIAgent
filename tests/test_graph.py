import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from agents.graph import run_workflow, resume_workflow

def test_full_workflow():
    print("\n--- test_full_workflow ---")
    thread_id = str(uuid.uuid4())

    # Step 1 — run workflow until human review
    print("Step 1: Running workflow...")
    state = run_workflow(
        user_input="Analyze my portfolio risk",
        portfolio_data="AAPL 40% 100 shares, MSFT 60% 50 shares",
        client_name="John Smith",
        thread_id=thread_id
    )
    print("Risk output preview:", state["risk_output"][:200])
    print("Client summary (should be empty):", state["client_summary"])

    # Step 2 — human approves
    print("\nStep 2: Human approving...")
    final_state = resume_workflow(
        thread_id=thread_id,
        approved=True,
        feedback=""
    )
    print("Client summary preview:", final_state["client_summary"][:300])
    print("✅ PASSED")

if __name__ == "__main__":
    print("=" * 50)
    print("Running WealthAdvisor Graph Tests")
    print("=" * 50)
    test_full_workflow()
    print("\n" + "=" * 50)
    print("✅ All graph tests passed!")
    print("=" * 50)