from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config.settings import get_settings
from tools.portfolio_tools import (
    get_stock_metrics,
    get_price_data,
    analyze_portfolio,
)

settings = get_settings()

FINANCIAL_PLANNER_PROMPT = """You are the WealthAdvisor Financial Planning Agent.
    You are an expert financial planner. Your job is to run scenario analyses and project portfolio outcomes.

    Always follow this sequence:
    1. Call analyze_portfolio to get current portfolio metrics
    2. Call get_price_data for each holding to get current prices and 1yr returns
    3. Call get_stock_metrics for each holding to get beta and sector

    Then produce exactly THREE scenarios:

    BEAR CASE (-20% market correction):
    - Project new portfolio value
    - Which holding gets hit hardest (highest beta)
    - Estimated recovery timeline

    BASE CASE (+10% annual return — historical average):
    - Project 1yr, 3yr, 5yr portfolio values
    - Compounded growth calculation

    BULL CASE (+25% market expansion):
    - Project new portfolio value
    - Best performing holding
    - Upside capture percentage

    After scenarios, give:
    - Rebalancing recommendation if any single holding > 40% weight
    - Time horizon suitability: short (< 1yr) / medium (1-3yr) / long (3yr+)

    Always show your calculations. Be specific with numbers.
"""

def build_planner_agent()->AgentExecutor:
    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.2
    )
    tools = [get_stock_metrics,get_price_data,analyze_portfolio]
    prompt = ChatPromptTemplate.from_messages([
        ("system", FINANCIAL_PLANNER_PROMPT),
        MessagesPlaceholder(variable_name="chat_history",optional=True),
        ("human","{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    agent = create_tool_calling_agent(llm,tools,prompt)
    return AgentExecutor(agent=agent,tools=tools,verbose=True,max_iterations=8)

def run_financial_planning(request: str, chat_history: list=None)->str:
    planner_agent = build_planner_agent()
    result = planner_agent.invoke({
        "input": request,
        "chat_history": chat_history or []
    })
    return result["output"]
