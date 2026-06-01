from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import get_settings

settings = get_settings()

def get_llm():
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0
    )

SUPERVISOR_PROMPT = """You are the WealthAdvisor AI Supervisor. 
    Your only job is to read the user's request and route it to the right specialist agent.

    Available agents:
    - risk_assessor: Analyzes portfolio risk, fetches SEC filings, calculates beta and sector exposure
    - financial_planner: Runs scenario analyses (bull/base/bear cases), projects future portfolio value
    - client_comms: Drafts personalized, human-readable summaries and client reports

    Rules:
    - Respond with ONLY one word — the agent name. Nothing else.
    - If the request involves risk, SEC filings, or portfolio metrics → risk_assessor
    - If the request involves projections, scenarios, or planning → financial_planner
    - If the request involves drafting a summary or client communication → client_comms
    - If unclear → risk_assessor
    """

def route_request(user_message: str)->str:
    llm = get_llm()
    messages = [
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=user_message)
    ]
    llm_response = llm.invoke(messages)
    agent_name = llm_response.content.strip().lower()
    valid = {"risk_assessor", "financial_planner", "client_comms"}
    return agent_name if agent_name in valid else "risk_assessor"