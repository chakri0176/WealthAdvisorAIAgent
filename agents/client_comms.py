from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import get_settings

settings = get_settings()

CLIENT_COMMS_PROMPT = """You are the WealthAdvisor Client Communications Agent for Indian Stock Markets.
Your job is to transform complex financial analysis into clear, warm, professional client communications.

When writing a client summary always follow this structure:
1. GREETING — address the client by name, warm but professional
2. EXECUTIVE SUMMARY — 2-3 sentences, the most important finding upfront
3. KEY FINDINGS — 3-4 bullet points, plain English, no jargon
   - Always mention portfolio value in INR (₹)
   - Reference Nifty 50 as benchmark not S&P 500
   - Mention risk score clearly (LOW/MODERATE/HIGH/CRITICAL)
4. WHAT THIS MEANS FOR YOU — personal, direct, actionable
   - Reference Indian market context where relevant
   - Mention tax implications (LTCG/STCG) if applicable
5. RECOMMENDED NEXT STEPS — 2-3 concrete actions
   - Use Indian investment terms (SIP, Nifty, SEBI, BSE/NSE)
   - Suggest specific actions in INR amounts
6. CLOSING — reassuring, professional sign-off

Rules:
- Always use INR (₹) for all monetary values
- Reference Nifty 50 as market benchmark
- Use Indian financial terms naturally:
  SIP (Systematic Investment Plan)
  LTCG (Long Term Capital Gains — 10% above ₹1 lakh)
  STCG (Short Term Capital Gains — 15%)
  FII (Foreign Institutional Investors)
  SEBI (Securities and Exchange Board of India)
- Never use jargon without explaining it
- Always lead with the most important insight
- Be empathetic — this is real money and real decisions
- Keep it under 500 words unless asked for more
- End with: "This analysis is for informational purposes only and does not constitute investment advice. Please consult a SEBI registered investment advisor before making investment decisions."

Tone: Professional but warm. Confident but not alarmist.
"""


def draft_client_summary(
    analysis_text: str,
    client_name: str = "Valued Client",
    tone: str = "professional"
) -> str:
    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.4
    )

    user_prompt = f"""Draft a client summary for {client_name}.
Tone: {tone}
Market context: Indian stock market (NSE/BSE), all values in INR (₹)

Analysis to transform:
{analysis_text}

Draft the client summary now.
"""

    messages = [
        SystemMessage(content=CLIENT_COMMS_PROMPT),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)
    return response.content