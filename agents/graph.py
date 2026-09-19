"""
WealthAdvisor LangGraph Workflow — Indian Stock Markets

Graph structure:
  START → supervisor → [risk_assessor | financial_planner | client_comms]
                     ↓
               human_review (interrupt)
                     ↓
               client_comms → END
"""
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import HumanMessage, AIMessage
import operator

from agents.supervisor import route_request
from agents.risk_assessor import run_risk_assessment
from agents.financial_planner import run_financial_planning
from agents.client_comms import draft_client_summary


# ── State definition ──────────────────────────────────────────────────────────

class WealthAdvisorState(TypedDict):
    messages: Annotated[list, operator.add]   # full conversation history
    user_input: str                            # current user request
    portfolio_data: str                        # raw portfolio description
    risk_output: str                           # risk assessor output
    planning_output: str                       # financial planner output
    client_summary: str                        # final client communication
    next_agent: str                            # supervisor routing decision
    human_approved: bool                       # human-in-the-loop gate
    client_name: str                           # for personalization
    client_id: str                             # links to SQLite memory
    client_profile: dict                       # loaded from SQLite
    session_history: list                      # past sessions from SQLite


# ── Node functions ────────────────────────────────────────────────────────────

def supervisor_node(state: WealthAdvisorState) -> WealthAdvisorState:
    """Route the request to the correct specialist agent."""
    decision = route_request(state["user_input"])
    return {**state, "next_agent": decision}


def risk_assessor_node(state: WealthAdvisorState) -> WealthAdvisorState:
    """Run Indian portfolio risk assessment using BSE filings."""
    output = run_risk_assessment(
        portfolio_description=state["portfolio_data"] or state["user_input"],
        chat_history=state.get("messages", []),
    )
    return {
        **state,
        "risk_output": output,
        "messages": state["messages"] + [AIMessage(content=f"[Risk Assessment]\n{output}")],
    }


def financial_planner_node(state: WealthAdvisorState) -> WealthAdvisorState:
    """Run Indian market financial scenario analysis in INR."""
    output = run_financial_planning(
        request=state["portfolio_data"] or state["user_input"],
        chat_history=state.get("messages", []),
    )
    return {
        **state,
        "planning_output": output,
        "messages": state["messages"] + [AIMessage(content=f"[Financial Planning]\n{output}")],
    }


def human_review_node(state: WealthAdvisorState) -> WealthAdvisorState:
    """
    Human-in-the-loop interrupt.
    Execution pauses here until a human approves or provides feedback.
    """
    analysis = ""
    if state.get("risk_output"):
        analysis += f"RISK ANALYSIS:\n{state['risk_output']}\n\n"
    if state.get("planning_output"):
        analysis += f"FINANCIAL PLANNING:\n{state['planning_output']}\n\n"

    human_decision = interrupt({
        "message": "Please review the analysis and approve or provide feedback.",
        "analysis": analysis,
    })

    approved = human_decision.get("approved", False)
    feedback = human_decision.get("feedback", "")

    updated_input = state["user_input"]
    if feedback:
        updated_input += f"\n\nAdvisor feedback: {feedback}"

    return {
        **state,
        "human_approved": approved,
        "user_input": updated_input
    }


def client_comms_node(state: WealthAdvisorState) -> WealthAdvisorState:
    """Draft the final client summary in Indian market context."""
    combined_analysis = ""
    if state.get("risk_output"):
        combined_analysis += f"RISK ANALYSIS:\n{state['risk_output']}\n\n"
    if state.get("planning_output"):
        combined_analysis += f"FINANCIAL PLANNING:\n{state['planning_output']}\n\n"
    if not combined_analysis:
        combined_analysis = state["user_input"]

    summary = draft_client_summary(
        analysis_text=combined_analysis,
        client_name=state.get("client_name", "Valued Client"),
    )
    return {
        **state,
        "client_summary": summary,
        "messages": state["messages"] + [AIMessage(content=f"[Client Summary]\n{summary}")],
    }


# ── Routing logic ─────────────────────────────────────────────────────────────

def route_after_supervisor(state: WealthAdvisorState) -> Literal["risk_assessor", "financial_planner", "client_comms"]:
    return state["next_agent"]


def route_after_review(state: WealthAdvisorState) -> Literal["client_comms", "risk_assessor"]:
    return "client_comms" if state.get("human_approved", False) else "risk_assessor"


# ── Build graph ───────────────────────────────────────────────────────────────

def build_graph():
    builder = StateGraph(WealthAdvisorState)

    # Add nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("risk_assessor", risk_assessor_node)
    builder.add_node("financial_planner", financial_planner_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("client_comms", client_comms_node)

    # Entry point
    builder.add_edge(START, "supervisor")

    # Supervisor routes to specialist agents
    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "risk_assessor": "risk_assessor",
            "financial_planner": "financial_planner",
            "client_comms": "client_comms",
        }
    )

    # After risk/planning → human review
    builder.add_edge("risk_assessor", "human_review")
    builder.add_edge("financial_planner", "human_review")

    # After human review → client comms or retry
    builder.add_conditional_edges(
        "human_review",
        route_after_review,
        {
            "client_comms": "client_comms",
            "risk_assessor": "risk_assessor",
        }
    )

    # Client comms → END
    builder.add_edge("client_comms", END)

    # Compile with memory for state persistence
    memory = MemorySaver()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["human_review"]
    )


# Singleton graph instance
graph = build_graph()


def run_workflow(
    user_input: str,
    portfolio_data: str = "",
    client_name: str = "Valued Client",
    client_id: str = "default",
    thread_id: str = "default",
) -> dict:
    """
    Run the full WealthAdvisor workflow for Indian stocks.
    Returns the final state including all outputs.
    """
    initial_state = WealthAdvisorState(
        messages=[HumanMessage(content=user_input)],
        user_input=user_input,
        portfolio_data=portfolio_data,
        risk_output="",
        planning_output="",
        client_summary="",
        next_agent="",
        human_approved=False,
        client_name=client_name,
        client_id=client_id,
        client_profile={},
        session_history=[],
    )
    config = {"configurable": {"thread_id": thread_id}}
    final_state = graph.invoke(initial_state, config=config)
    return final_state


def resume_workflow(
    thread_id: str,
    approved: bool,
    feedback: str = ""
) -> dict:
    """
    Resume after human review interrupt.
    Call this after the human has reviewed and approved/rejected the analysis.
    """
    config = {"configurable": {"thread_id": thread_id}}
    final_state = graph.invoke(
        Command(resume={"approved": approved, "feedback": feedback}),
        config=config
    )
    return final_state