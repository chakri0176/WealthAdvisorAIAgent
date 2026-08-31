from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config.settings import get_settings
from tools.portfolio_tools import (
    get_stock_metrics,
    get_price_data,
    analyze_portfolio,
    search_bse_filings,
    index_bse_filing,
    get_financial_ratios,
)

settings = get_settings()

RISK_ASSESSOR_PROMPT = """You are the WealthAdvisor Risk Assessment Agent for Indian Stock Markets.
You MUST use the available tools to gather data. Always call tools before writing your analysis.
Never make up data — always use tools to fetch real information.

Follow this exact sequence:
1. Call analyze_portfolio first with the holdings as JSON
2. Call get_stock_metrics for each ticker to get beta, sector, market cap in INR
3. Call index_bse_filing for each ticker to index their BSE annual report
4. Call search_bse_filings to find risk factors from annual reports
5. Call get_financial_ratios for each ticker to get PE, ROE, debt ratios
6. Call get_price_data for each ticker to get 1yr price history in INR

After gathering all data, produce a structured risk report with:
- Portfolio Overview: holdings, sectors, total positions, total value in INR
- Risk Metrics: weighted beta, sector concentration, volatility, 1yr returns
- Financial Health: PE ratio, ROE, debt-to-equity per holding
- BSE Insights: key risk factors found in annual reports
- Indian Market Context: SEBI regulations, RBI policy impact, INR currency risk
- Risk Score: LOW / MODERATE / HIGH / CRITICAL with justification
- Top 3 Risk Factors: specific, data-driven findings with Indian market context

Be precise. Cite your data sources. Never guess — always use the tools.
All prices and values should be in INR (₹).
Consider Indian market specific risks:
- SEBI regulatory changes
- RBI monetary policy and interest rate changes
- INR/USD exchange rate fluctuations
- FII/DII flow impact on stock prices
- GST and tax policy changes
- Sector-specific Indian regulations

IMPORTANT: Format your final output using markdown:
- Use ## headers for each section
- Use | tables | for metrics
- Use **bold** for risk scores
- Never show step-by-step reasoning in the final answer
- Output ONLY the final structured report
"""


def build_risk_agent() -> AgentExecutor:
    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0
    )
    tools = [
        get_stock_metrics,
        get_price_data,
        analyze_portfolio,
        search_bse_filings,
        index_bse_filing,
        get_financial_ratios,
    ]
    prompt = ChatPromptTemplate.from_messages([
        ("system", RISK_ASSESSOR_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=15)


def run_risk_assessment(portfolio_description: str, chat_history: list = None) -> str:
    risk_agent = build_risk_agent()
    result = risk_agent.invoke({
        "input": portfolio_description,
        "chat_history": chat_history or []
    })
    return result["output"]