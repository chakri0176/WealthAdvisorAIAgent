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

class WealthAdvisorState(TypedDict):
    messages: Annotated[list, operator.add]  # conversation history
    user_input: str                           # original user request
    portfolio_data: str                       # portfolio description
    risk_output: str                          # risk assessor writes here
    planning_output: str                      # financial planner writes here
    client_summary: str                       # client comms writes here
    next_agent: str                           # supervisor's routing decision
    human_approved: bool                      # human review gate
    client_name: str                          # for personalization
    client_id: str           # unique client identifier
    client_profile: dict     # full client profile from DB
    session_history: list    # previous analyses this session
    
def supervisor_node(state: WealthAdvisorState) -> WealthAdvisorState:
    decision = route_request(state["user_input"])
    return {**state, "next_agent": decision}

def risk_assessor_node(state: WealthAdvisorState)->WealthAdvisorState:
    risk_output = run_risk_assessment(
        portfolio_description = state["portfolio_data"] or state["user_input"],
        chat_history = state["messages"]
    )
    return {
    **state,
        "risk_output": risk_output,
        "messages": state["messages"] + [AIMessage(content=risk_output)]
    }
    
def financial_planner_node(state: WealthAdvisorState)->WealthAdvisorState:
    planning_output = run_financial_planning(
        request = state["portfolio_data"] or state["user_input"],
        chat_history = state["messages"]
    )
    return{
        **state,
        "planning_output": planning_output,
        "messages": state["messages"] + [AIMessage(content=planning_output)]
    }
    
def human_review_node(state: WealthAdvisorState) -> WealthAdvisorState:
    # Combine all analysis produced so far
    analysis = ""
    if state.get("risk_output"):
        analysis += f"RISK ANALYSIS:\n{state['risk_output']}\n\n"
    if state.get("planning_output"):
        analysis += f"FINANCIAL PLANNING:\n{state['planning_output']}\n\n"

    # This PAUSES the graph and waits for human input
    human_decision = interrupt({
        "message": "Please review the analysis and approve or provide feedback.",
        "analysis": analysis,
    })

    approved = human_decision.get("approved", False)
    feedback = human_decision.get("feedback", "")

    # If feedback given, append it to user input for regeneration
    updated_input = state["user_input"]
    if feedback:
        updated_input += f"\n\nAdvisor feedback: {feedback}"

    return {
        **state,
        "human_approved": approved,
        "user_input": updated_input
    }
    
def client_comms_node(state: WealthAdvisorState)->WealthAdvisorState:
    combined_analysis = ""
    if state["risk_output"]:
        combined_analysis+=f"RISK ANALYSIS:\n{state['risk_output']}\n\n"
    if state["planning_output"]:
        combined_analysis+=f"FINANCIAL PLANNING:\n{state['planning_output']}\n\n"
    if not combined_analysis:
        combined_analysis+=state["user_input"]
        
    client_summary = draft_client_summary(
        analysis_text = combined_analysis,
        client_name = state.get("client_name","Valued Client")
    )
    return{
        **state,
        "client_summary": client_summary,
        "messages": state["messages"] + [AIMessage(content=client_summary)]
    }
    
def route_after_supervisor(state: WealthAdvisorState)->Literal["risk_assessor","financial_planner_client_comms"]:
    return state["next_agent"]

def route_after_review(state: WealthAdvisorState)->Literal["client_comms","risk_assessor"]:
    return "client_comms" if state.get("human_approved",False) else "risk_assessor"

def build_graph():
    # 1. Create the graph builder with our state
    builder = StateGraph(WealthAdvisorState)

    # 2. Add all nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("risk_assessor", risk_assessor_node)
    builder.add_node("financial_planner", financial_planner_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("client_comms", client_comms_node)

    # 3. Entry point — always start at supervisor
    builder.add_edge(START, "supervisor")

    # 4. Supervisor routes to one of three agents
    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "risk_assessor": "risk_assessor",
            "financial_planner": "financial_planner",
            "client_comms": "client_comms",
        }
    )

    # 5. After risk/planning → human review
    builder.add_edge("risk_assessor", "human_review")
    builder.add_edge("financial_planner", "human_review")

    # 6. After human review → client comms or retry
    builder.add_conditional_edges(
        "human_review",
        route_after_review,
        {
            "client_comms": "client_comms",
            "risk_assessor": "risk_assessor",
        }
    )

    # 7. Client comms → END
    builder.add_edge("client_comms", END)

    # 8. Compile with memory for state persistence
    memory = MemorySaver()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["human_review"]
    )

# Create graph instance
graph = build_graph()


def run_workflow(
    user_input: str,
    portfolio_data: str="",
    client_name: str = "Valued Client",
    client_id: str = "default",
    thread_id: str = "default",
)->dict:
    initial_state = WealthAdvisorState(
        messages = [HumanMessage(content = user_input)],
        user_input = user_input,
        portfolio_data = portfolio_data,
        risk_output = "",
        planning_output = "",
        client_summary = "",
        next_agent = "",
        human_approved = False,
        client_name = client_name,
        client_id = client_id,
        client_profile = {},
        session_history = []
    )
    
    config = {"configurable":{"thread_id":thread_id}}
    final_state = graph.invoke(initial_state, config = config)
    return final_state

def resume_workflow(
    thread_id: str,
    approved: bool,
    feedback: str = ""
)->dict:
    config = {"configurable":{"thread_id":thread_id}}
    final_state = graph.invoke(
        Command(resume={"approved":approved,"feedback":feedback}),
        config=config
    )
    return final_state
