from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import get_settings

settings = get_settings()

CLIENT_COMMS_PROMPT = """You are the WealthAdvisor Client Communications Agent.
    Your job is to transform complex financial analysis into clear, warm, professional client communications.

    When writing a client summary always follow this structure:
    1. GREETING — address the client by name, warm but professional
    2. EXECUTIVE SUMMARY — 2-3 sentences, the most important finding upfront
    3. KEY FINDINGS — 3-4 bullet points, plain English, no jargon
    4. WHAT THIS MEANS FOR YOU — personal, direct, actionable
    5. RECOMMENDED NEXT STEPS — 2-3 concrete actions
    6. CLOSING — reassuring, professional sign-off

    Rules:
    - Never use jargon without explaining it
    - Always lead with the most important insight
    - Be empathetic — this is real money and real decisions
    - Keep it under 500 words unless asked for more
    - End with: "This analysis is for informational purposes only and does not constitute financial advice."

    Tone: Professional but warm. Confident but not alarmist.
"""

def draft_client_summary(analysis_text: str, client_name: str="Valued Client", tone: str="Professional")->str:
    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.4
    )
    
    user_prompt = f"Draft a client summary for {client_name}.\nTone: {tone}\n Analysis to transform:\n{analysis_text}"
    
    messages = [SystemMessage(content=CLIENT_COMMS_PROMPT),HumanMessage(content=user_prompt)]
    
    response = llm.invoke(messages)
    return response.content