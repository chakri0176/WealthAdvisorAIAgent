from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config.settings import get_settings
from tools.portfolio_tools import (
    get_stock_metrics,
    get_price_data,
    analyze_portfolio,
    search_sec_filings,
    index_sec_filing,
)

settings = get_settings()

RISK_ASSESSOR_PROMPT = """You are the WealthAdvisor Risk Assessment Agent.
You MUST use the available tools to gather data. Always call tools before writing your analysis.
Never make up data — always use tools to fetch real information.

Follow this exact sequence:
1. Call analyze_portfolio first with the holdings as JSON
2. Call get_stock_metrics for each ticker
3. Call index_sec_filing for each ticker
4. Call search_sec_filings to find risk factors
5. Call get_price_data for each ticker
6. Write your final risk report

After gathering all data, produce a structured risk report with:
- Portfolio Overview: holdings, sectors, total positions
- Risk Metrics: weighted beta, sector concentration, volatility
- SEC Insights: key risk factors found in filings
- Risk Score: LOW / MODERATE / HIGH / CRITICAL with justification
- Top 3 Risk Factors: specific, data-driven findings

Be precise. Cite your data sources. Never guess — always use the tools.

IMPORTANT: Format your final output using markdown:
- Use ## headers for each section
- Use | tables | for metrics
- Use **bold** for risk scores
- Never show step-by-step reasoning in the final answer
- Output ONLY the final structured report
"""

def build_risk_agent()->AgentExecutor:
    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0
    )
    tools = [get_stock_metrics,get_price_data,analyze_portfolio,search_sec_filings,index_sec_filing]
    prompt = ChatPromptTemplate.from_messages([
        ("system", RISK_ASSESSOR_PROMPT),
        MessagesPlaceholder(variable_name="chat_history",optional=True),
        ("human","{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    agent = create_tool_calling_agent(llm,tools,prompt)
    return AgentExecutor(agent=agent,tools=tools,verbose=True,max_iterations=15)
    
    
def run_risk_assessment(portfolio_description: str, chat_history: list=None)->str:
    risk_agent = build_risk_agent()
    result = risk_agent.invoke({
        "input": portfolio_description,
        "chat_history": chat_history or []
    })
    return result["output"]