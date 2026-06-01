from langchain_google_genai import ChatGoogleGenerativeAI
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