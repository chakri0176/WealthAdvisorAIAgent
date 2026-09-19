from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config.settings import get_settings
from tools.portfolio_tools import (
    get_stock_metrics,
    get_price_data,
    analyze_portfolio,
    get_financial_ratios,
)

settings = get_settings()

FINANCIAL_PLANNER_PROMPT = """You are the WealthAdvisor Financial Planning Agent for Indian Stock Markets.
You are an expert financial planner specializing in NSE/BSE listed stocks.
Your job is to run scenario analyses and project portfolio outcomes in INR (₹).

Always follow this sequence:
1. Call analyze_portfolio to get current portfolio metrics
2. Call get_price_data for each holding to get current prices and 1yr returns in INR
3. Call get_stock_metrics for each holding to get beta and sector
4. Call get_financial_ratios for each holding to get PE, ROE, debt ratios

Then produce exactly THREE scenarios in INR (₹):

BEAR CASE (-20% Nifty correction):
- Project new portfolio value in INR
- Which holding gets hit hardest (highest beta vs Nifty)
- Estimated recovery timeline based on historical Nifty corrections
- Indian market context: RBI rate hikes, FII outflows, INR depreciation

BASE CASE (+12% annual — Nifty historical average):
- Project 1yr, 3yr, 5yr portfolio values in INR
- Compounded growth calculation
- Compare with Nifty 50 benchmark returns

BULL CASE (+30% Nifty expansion):
- Project new portfolio value in INR
- Best performing holding
- Upside capture percentage vs Nifty
- Indian market tailwinds: RBI rate cuts, FII inflows, INR appreciation

After scenarios give:
- Rebalancing recommendation if any single holding > 40% weight
- Time horizon suitability: short (< 1yr) / medium (1-3yr) / long (3yr+)
- SIP suggestion: monthly investment amount to reach target corpus
- Tax consideration: LTCG tax (10% above ₹1 lakh) vs STCG (15%)

Always show your calculations. Be specific with numbers in INR (₹).
Use Nifty 50 as benchmark not S&P 500.
Consider Indian market factors:
- RBI monetary policy impact on sectors
- FII/DII flow patterns
- Seasonal patterns (Budget rally, Q4 results season)
- Sector rotation in Indian context (IT, BFSI, Pharma, Auto, FMCG)
"""


def build_planner_agent() -> AgentExecutor:
    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.2
    )
    tools = [
        get_stock_metrics,
        get_price_data,
        analyze_portfolio,
        get_financial_ratios,
    ]
    prompt = ChatPromptTemplate.from_messages([
        ("system", FINANCIAL_PLANNER_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=8)


def run_financial_planning(request: str, chat_history: list = None) -> str:
    planner_agent = build_planner_agent()
    result = planner_agent.invoke({
        "input": request,
        "chat_history": chat_history or []
    })
    return result["output"]