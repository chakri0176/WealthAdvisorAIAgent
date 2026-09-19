from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import get_settings

settings = get_settings()

def get_llm():
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0
    )

SUPERVISOR_PROMPT = """You are the WealthAdvisor AI Supervisor for Indian Stock Markets.
Your only job is to read the user's request and route it to the right specialist agent.

Available agents:
- risk_assessor: Analyzes portfolio risk, fetches BSE annual reports, calculates beta vs Nifty, sector exposure, SEBI compliance risks
- financial_planner: Runs scenario analyses (bull/base/bear cases), projects future portfolio value in INR, SIP planning, Nifty benchmark comparison
- client_comms: Drafts personalized, human-readable summaries and client reports in Indian market context

Rules:
- Respond with ONLY one word — the agent name. Nothing else.
- If the request involves risk, BSE filings, portfolio metrics, beta, sector → risk_assessor
- If the request involves projections, scenarios, SIP, planning, returns → financial_planner
- If the request involves drafting a summary or client communication → client_comms
- If unclear → risk_assessor
"""


def route_request(user_message: str) -> str:
    llm = get_llm()
    messages = [
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=user_message)
    ]
    llm_response = llm.invoke(messages)
    agent_name = llm_response.content.strip().lower()
    valid = {"risk_assessor", "financial_planner", "client_comms"}
    return agent_name if agent_name in valid else "risk_assessor"