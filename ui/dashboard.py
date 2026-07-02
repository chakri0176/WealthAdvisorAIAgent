"""
WealthAdvisor AI — Chat Dashboard v2
Run with: streamlit run ui/dashboard.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import requests
import json
import uuid

API_BASE = "http://localhost:8000"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WealthAdvisor AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f1117; color: #c9d1d9; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #21262d; }

    /* Chat messages */
    .chat-user {
        background: #1f6feb22;
        border: 1px solid #1f6feb55;
        border-radius: 12px 12px 2px 12px;
        padding: 12px 16px;
        margin: 8px 0 8px 60px;
        color: #c9d1d9;
    }
    .chat-agent {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 2px 12px 12px 12px;
        padding: 12px 16px;
        margin: 8px 60px 8px 0;
        color: #c9d1d9;
    }
    .chat-system {
        background: #1a2f1a;
        border: 1px solid #3fb95055;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 6px 0;
        color: #3fb950;
        font-size: 13px;
    }
    .chat-label-user {
        font-size: 11px;
        color: #58a6ff;
        font-weight: 600;
        margin-bottom: 4px;
        text-align: right;
    }
    .chat-label-agent {
        font-size: 11px;
        color: #8b949e;
        font-weight: 600;
        margin-bottom: 4px;
    }

    /* Review card */
    .review-card {
        background: #2d2208;
        border: 1px solid #e3b34155;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }

    /* Metric cards */
    .metric-row {
        display: flex;
        gap: 8px;
        margin: 8px 0;
    }

    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "awaiting_review" not in st.session_state:
    st.session_state.awaiting_review = False
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "last_client" not in st.session_state:
    st.session_state.last_client = ""

# ── Helper functions ──────────────────────────────────────────────────────────
def check_api():
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=3)
        return resp.status_code == 200
    except:
        return False

def reset_session():
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.session_state.awaiting_review = False
    st.session_state.analysis_result = None
    st.session_state.analysis_complete = False

def is_relevant_question(question: str, llm) -> bool:
    """Check if the question is related to finance/stocks/wealth management or conversation."""
    from langchain_core.messages import HumanMessage, SystemMessage
    
    check_messages = [
        SystemMessage(content="""You are a strict topic classifier.
Respond with ONLY one word: YES or NO.

Say YES if the question is:
- Related to stocks, shares, equities, portfolio
- Related to wealth management or financial planning
- Related to SEC filings or company financials
- Related to market data, prices, returns, risk
- A follow-up to a previous message (e.g. "what did I ask?", "tell me more", "explain that", "what was my question?", "summarize our conversation")
- A greeting or general conversation starter (e.g. "hello", "hi", "thanks")

Say NO if the question is:
- About politics, sports, entertainment, or general knowledge
- Completely unrelated to finance or the current conversation
- Asking for jokes, stories, or creative writing
"""),
        HumanMessage(content=question)
    ]
    response = llm.invoke(check_messages)
    return response.content.strip().upper().startswith("YES")

def get_chat_agent():
    from langchain_groq import ChatGroq
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from tools.portfolio_tools import get_stock_metrics, get_price_data
    from config.settings import get_settings
    from clients.client_memory import load_client_history, get_client_profile
    
    settings = get_settings()
    
    profile = get_client_profile(client_id)
    history = load_client_history(client_id,limit=5)
    
    #build history context
    history_context = ""
    if history:
        history_context = """
        IMPORTANT: The following is CLIENT HISTORY DATA from our database. 
        Do NOT use any tools on this data. Just read and reference it directly.

        PREVIOUS ANALYSIS SESSIONS:
        """
        for h in history:
            history_context += f"[Session on {h['created_at'][:10]}]: Risk Score was {h['risk_score']}\n"
        history_context += f"Total past sessions: {len(history)}\n"
        history_context += "END OF CLIENT HISTORY - Do not call any tools on the above data.\n"
        
    profile_context = ""
    if profile:
        profile_context = f"Risk Tolerance: {profile['risk_tolerance']}\nGoals: {profile['investment_goals']}\nTime Horizon: {profile['time_horizon']}"
    
    llm = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.3
    )
    
    # Only give it lightweight tools — no SEC indexing (that's slow)
    tools = [get_stock_metrics, get_price_data]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are WealthAdvisor AI, specialized ONLY in stocks and wealth management.
        You have access to LIVE market data tools — use them when asked about prices or metrics.
        NEVER say you cannot access real-time data. You CAN via your tools.
        Refuse any questions not related to stocks, portfolios, or wealth management.

        CLIENT INFORMATION:
        Name: {client_name}
        ID: {client_id}
        {profile_context}
        
        {history_context}

        Use this context to give personalized responses. Reference past sessions when relevant.
        """),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,      # no verbose for chat
        max_iterations=3    # max 3 tool calls — keeps it fast
    )

def add_message(role: str, content: str, msg_type: str = "text"):
    st.session_state.chat_history.append({
        "role": role,
        "content": content,
        "type": msg_type
    })


def render_chat():
    for msg in st.session_state.chat_history:
        content = msg["content"].replace("$",r"\$")
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-label-user">You</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-user">{content}</div>', unsafe_allow_html=True)
        elif msg["role"] == "agent":
            st.markdown(f'<div class="chat-label-agent">🤖 WealthAdvisor</div>', unsafe_allow_html=True)
            if msg.get("type") == "markdown":
                with st.container():
                    st.markdown(content)
            else:
                st.markdown(f'<div class="chat-agent">{content}</div>', unsafe_allow_html=True)
        elif msg["role"] == "system":
            st.markdown(f'<div class="chat-system">⚙️ {content}</div>', unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 WealthAdvisor AI")
    st.caption("Multi-Agent Wealth Management")

    api_ok = check_api()
    if api_ok:
        st.success("API Connected", icon="✅")
    else:
        st.error("API Offline", icon="❌")
        st.caption("Run: `uvicorn api.main:app --port 8000`")

    st.divider()

    # Client details
    st.subheader("👤 Client")
    client_name = st.text_input("Name", value="John Smith", key="client_name_input")
    client_id = st.text_input("ID", value="client_001", key="client_id_input")

    # Reset if client changes
    if st.session_state.last_client != client_name:
        st.session_state.last_client = client_name
        reset_session()

    st.divider()

    # Portfolio input
    st.subheader("💼 Portfolio")
    num_holdings = st.number_input("Holdings", min_value=1, max_value=10, value=3)

    holdings = []
    total_weight = 0.0

    for i in range(num_holdings):
        c1, c2, c3 = st.columns([2, 1, 1])
        ticker = c1.text_input("Ticker", key=f"t_{i}",
            value=["AAPL", "MSFT", "GOOGL"][i] if i < 3 else "",
            label_visibility="collapsed", placeholder="AAPL")
        weight = c2.number_input("W%", key=f"w_{i}",
            value=[40.0, 35.0, 25.0][i] if i < 3 else 0.0,
            min_value=0.0, max_value=100.0,
            label_visibility="collapsed")
        shares = c3.number_input("Shares", key=f"s_{i}",
            value=[100, 50, 30][i] if i < 3 else 0,
            min_value=0, label_visibility="collapsed")
        if ticker.strip():
            holdings.append({"ticker": ticker.upper().strip(),
                             "weight": round(weight / 100, 4),
                             "shares": shares})
            total_weight += weight

    if total_weight != 100:
        st.warning(f"Weight: {total_weight:.1f}% ≠ 100%")
    else:
        st.success(f"Weight: {total_weight:.0f}% ✅")

    # Portfolio chart in sidebar
    if holdings and total_weight == 100:
        fig = px.pie(
            values=[h["weight"] * 100 for h in holdings],
            names=[h["ticker"] for h in holdings],
            color_discrete_sequence=["#58a6ff", "#3fb950", "#e3b341", "#f85149", "#d2a8ff"],
            hole=0.5,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9",
            showlegend=True,
            legend_font_color="#8b949e",
            margin=dict(t=10, b=10, l=10, r=10),
            height=200,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Analysis type
    st.subheader("🎯 Analysis Type")
    analysis_type = st.selectbox("Type", [
        "Full Analysis (Risk + Planning)",
        "Risk Assessment Only",
        "Scenario Planning Only",
    ], label_visibility="collapsed")

    # Run Analysis button
    can_run = total_weight == 100 and len(holdings) > 0 and api_ok
    if st.button("🚀 Run Full Analysis", type="primary",
                  use_container_width=True, disabled=not can_run):
        prompt_map = {
            "Full Analysis (Risk + Planning)": "Perform a complete risk assessment and financial scenario analysis for this portfolio.",
            "Risk Assessment Only": "Perform a detailed risk assessment of this portfolio including SEC filing analysis.",
            "Scenario Planning Only": "Run bull, base, and bear case scenario analyses for this portfolio.",
        }
        user_msg = f"Run {analysis_type} for my portfolio: {json.dumps(holdings)}"
        add_message("user", f"Please run a **{analysis_type}** for my portfolio.")
        add_message("system", "Analysis started — agents are working...")

        with st.spinner("Agents analyzing..."):
            try:
                resp = requests.post(f"{API_BASE}/analyze", json={
                    "user_input": prompt_map[analysis_type],
                    "portfolio_data": f"Portfolio: {json.dumps(holdings)}",
                    "client_name": client_name,
                    "client_id": client_id,
                    "thread_id": st.session_state.thread_id,
                }, timeout=300)
                resp.raise_for_status()
                result = resp.json()
                st.session_state.analysis_result = result
                st.session_state.awaiting_review = result.get("status") == "awaiting_review"

                # Add results to chat
                if result.get("risk_output"):
                    add_message("agent", result["risk_output"], msg_type="markdown")
                if result.get("planning_output"):
                    add_message("agent", result["planning_output"], msg_type="markdown")
                if st.session_state.awaiting_review:
                    add_message("system", "Analysis complete — awaiting your review below.")
                st.rerun()
            except Exception as e:
                add_message("system", f"Analysis failed: {str(e)}")
                st.rerun()

    st.divider()

    # New session
    if st.button("🔄 New Session", use_container_width=True):
        reset_session()
        st.rerun()

    st.caption(f"Session: `{st.session_state.thread_id[:10]}...`")

# ── MAIN AREA — Chat Interface ────────────────────────────────────────────────
st.markdown("### 💬 WealthAdvisor Chat")
st.caption(f"Client: **{client_name}** · Powered by LangGraph + Groq GPT-OSS 120B")
st.divider()

# Welcome message
if not st.session_state.chat_history:
    st.markdown(f"""
    <div class="chat-label-agent">🤖 WealthAdvisor</div>
    <div class="chat-agent">
        Hello <strong>{client_name}</strong>! 👋<br><br>
        I'm your AI wealth advisor. I can help you with:<br>
        • <strong>Portfolio risk assessment</strong> — beta, sector concentration, SEC filing analysis<br>
        • <strong>Scenario planning</strong> — bull, base, and bear case projections<br>
        • <strong>Client summaries</strong> — professional reports for your clients<br><br>
        Use the <strong>sidebar</strong> to set up your portfolio and run a full analysis,
        or just <strong>chat with me</strong> below for quick questions!
    </div>
    """, unsafe_allow_html=True)

# Render chat history
render_chat()

# ── Human review gate (in chat) ───────────────────────────────────────────────
if st.session_state.awaiting_review and not st.session_state.analysis_complete:
    st.markdown("""
    <div class="review-card">
        <strong>⚠️ Advisor Review Required</strong><br>
        The analysis is complete. Please review and approve before generating the client summary.
    </div>
    """, unsafe_allow_html=True)

    feedback = st.text_area("Feedback (optional — leave blank to approve as-is)",
                             placeholder="e.g. Focus more on tech concentration risk...",
                             key="review_feedback")

    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("✅ Approve", type="primary", use_container_width=True):
            add_message("user", "✅ Approved — please generate the client summary.")
            with st.spinner("Generating client summary..."):
                try:
                    resp = requests.post(f"{API_BASE}/review", json={
                        "thread_id": st.session_state.thread_id,
                        "approved": True,
                        "feedback": feedback,
                    }, timeout=120)
                    resp.raise_for_status()
                    result = resp.json()
                    st.session_state.analysis_result = result
                    st.session_state.awaiting_review = False
                    st.session_state.analysis_complete = True
                    if result.get("client_summary"):
                        add_message("agent", result["client_summary"], msg_type="markdown")
                        add_message("system", "✅ Client summary generated successfully!")
                    st.rerun()
                except Exception as e:
                    add_message("system", f"Error: {str(e)}")
                    st.rerun()

    with col2:
        if st.button("🔁 Regenerate", use_container_width=True):
            if not feedback.strip():
                st.warning("Please provide feedback first.")
            else:
                add_message("user", f"Please regenerate with this feedback: {feedback}")
                with st.spinner("Regenerating..."):
                    try:
                        resp = requests.post(f"{API_BASE}/review", json={
                            "thread_id": st.session_state.thread_id,
                            "approved": False,
                            "feedback": feedback,
                        }, timeout=300)
                        resp.raise_for_status()
                        result = resp.json()
                        st.session_state.analysis_result = result
                        if result.get("risk_output"):
                            add_message("agent", result["risk_output"], msg_type="markdown")
                        add_message("system", "Analysis regenerated — awaiting review.")
                        st.rerun()
                    except Exception as e:
                        add_message("system", f"Error: {str(e)}")
                        st.rerun()

# ── Download button ───────────────────────────────────────────────────────────
if st.session_state.analysis_complete and st.session_state.analysis_result:
    summary = st.session_state.analysis_result.get("client_summary", "")
    if summary:
        st.divider()
        st.download_button(
            label="📥 Download Client Summary",
            data=summary,
            file_name=f"wealth_summary_{client_name.replace(' ', '_')}.txt",
            mime="text/plain",
        )

# ── Chat input ────────────────────────────────────────────────────────────────
st.divider()

with st.form("chat_form", clear_on_submit=True):
    col_input, col_send = st.columns([6, 1])
    user_input = col_input.text_input(
        "Message",
        placeholder="Ask me anything about your portfolio... e.g. 'What's my biggest risk?'",
        label_visibility="collapsed"
    )
    send = col_send.form_submit_button("Send", use_container_width=True)

    if send and user_input.strip():
        add_message("user", user_input)
        with st.spinner("Thinking..."):
            try:
                from langchain_groq import ChatGroq
                from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
                from config.settings import get_settings
                settings = get_settings()

                llm = ChatGroq(
                    model=settings.groq_model,
                    api_key=settings.groq_api_key,
                    temperature=0.3
                )

                if not is_relevant_question(user_input, llm):
                    add_message("agent",
                        "I'm specialized in **stock analysis and wealth management** only. "
                        "I can't answer general questions outside of finance. "
                        "Try asking me about your portfolio risk, stock metrics, "
                        "scenario analysis, or SEC filings! 📈")
                    st.rerun()
                from langchain_core.messages import HumanMessage, AIMessage
                langchain_history = []
                for msg in st.session_state.chat_history:
                    if msg["role"] == "user":
                        langchain_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "agent":
                        content = msg["content"][:500] + "..." if len(msg["content"]) > 500 else msg["content"]
                        langchain_history.append(AIMessage(content=content))
                chat_agent = get_chat_agent()
                result = chat_agent.invoke({
                    "input": user_input,
                    "chat_history": langchain_history
                })
                add_message("agent", result["output"], msg_type="markdown")

            except Exception as e:
                add_message("agent", f"Sorry, I encountered an error: {str(e)}")
        st.rerun()
# ── Footer ────────────────────────────────────────────────────────────────────
st.caption("WealthAdvisor AI · For informational purposes only · Not financial advice")