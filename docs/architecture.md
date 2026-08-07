# WealthAdvisor AI — Architecture Deep Dive

## Overview

WealthAdvisor AI is built on a **multi-agent architecture** using LangGraph 1.1. Instead of one large AI model doing everything, specialized agents each handle one domain — coordinated by a supervisor.

This mirrors how a real wealth management firm works:
- **Relationship manager** (supervisor) — understands client needs and routes
- **Risk analyst** (risk assessor) — digs into numbers and SEC filings
- **Financial planner** (financial planner) — models future scenarios
- **Client advisor** (client comms) — communicates findings clearly
- **Memory** (SQLite) — remembers every client across sessions

---

## Current Tech Stack (July 2026)

| Layer | Technology | Notes |
|-------|-----------|-------|
| Agent Orchestration | LangGraph 1.1.0 | Sequential now, parallel planned |
| LLM (agents) | Groq + LLaMA 3.3 70B versatile | Free, high RPM, tool-calling optimized |
| LLM (chat) | Groq + GPT-OSS 120B | High capability financial reasoning |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | 100% local — no API quota |
| Vector DB | ChromaDB 0.5.23 | Local persistent storage, 384-dim |
| Market Data | yfinance | Live prices, beta, sector data |
| SEC Data | SEC EDGAR API | Free US government filing API |
| HTML Parsing | BeautifulSoup4 | Strips HTML from raw SEC filings |
| Client Memory | SQLite | Persistent client profiles + history |
| API | FastAPI 0.115 | Async REST, auto Swagger docs |
| Dashboard | Streamlit 1.35 + Plotly | Chat interface + portfolio charts |

---

## Why These Technology Choices

### Why Groq instead of OpenAI/Gemini?

During development:
- **Gemini 3.1 Pro** → paid only (removed from free tier April 2026)
- **Gemini 2.5 Flash** → free but only 5 RPM — too slow for multi-tool agents
- **OpenAI GPT-4o** → deprecated February 2026
- **Groq** → free, 100+ RPM, specifically optimized for tool calling, 500 tokens/sec

### Why HuggingFace embeddings instead of Gemini?

Gemini embedding API hit rate limits when indexing multiple SEC filings (63 chunks × 3 companies = 189 API calls per analysis). HuggingFace MiniLM:
- Runs **100% locally** — no API calls ever
- No quota limits — index as many filings as needed
- Downloads once (~90MB), cached forever
- Fast enough for production (5-8 seconds per filing)
- 384-dimension vectors — accurate for financial text

### Why SQLite instead of PostgreSQL?

For the current scale (single advisor, multiple clients), SQLite is perfect:
- Zero setup — built into Python
- No separate database server needed
- File-based — easy to backup and migrate
- Handles hundreds of clients without issues
- Migrate to PostgreSQL when scaling to thousands of users

---

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT DASHBOARD                       │
│                                                             │
│  ┌──────────────┐    ┌──────────────────────────────────┐  │
│  │   Sidebar    │    │         Chat Interface            │  │
│  │              │    │                                  │  │
│  │ Client Info  │    │  Welcome message                 │  │
│  │ Portfolio    │    │  Chat history (scrollable)       │  │
│  │ Holdings     │    │  Human review gate               │  │
│  │              │    │  Message input + Send button     │  │
│  │ [Run         │    │  Download summary button         │  │
│  │  Analysis]   │    │                                  │  │
│  └──────────────┘    └──────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP POST /analyze
                          │ HTTP POST /review
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                          │
│                                                             │
│  GET  /health    → returns {"status": "ok"}                │
│  POST /analyze   → starts LangGraph workflow               │
│  POST /review    → resumes after human interrupt           │
│                                                             │
│  Auto-saves to SQLite after each analysis                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  LANGGRAPH WORKFLOW                         │
│                                                             │
│  START → supervisor → risk_assessor → human_review         │
│                    → financial_planner → human_review       │
│                    → client_comms → END                    │
│                                                             │
│  MemorySaver: saves state at every step                    │
│  interrupt_before=["human_review"]: pauses for approval    │
└────────────┬──────────────────────────────────────────────┘
             │
     ┌───────┴────────┐
     ▼                ▼
┌──────────┐    ┌──────────────┐
│  DATA    │    │   CLIENT     │
│  LAYER   │    │   MEMORY     │
│          │    │              │
│ yfinance │    │ SQLite DB    │
│ SEC EDGAR│    │              │
│ ChromaDB │    │ • Profiles   │
│ MiniLM   │    │ • Sessions   │
└──────────┘    └──────────────┘
```

---

## LangGraph Workflow Detail

### State Object

```python
class WealthAdvisorState(TypedDict):
    messages: Annotated[list, operator.add]  # conversation history
    user_input: str                           # current user request
    portfolio_data: str                       # portfolio description
    risk_output: str                          # risk assessor fills this
    planning_output: str                      # financial planner fills this
    client_summary: str                       # client comms fills this
    next_agent: str                           # supervisor's routing decision
    human_approved: bool                      # human review gate result
    client_name: str                          # for personalization
    client_id: str                            # links to SQLite memory
    client_profile: dict                      # loaded from SQLite
    session_history: list                     # past sessions from SQLite
```

### Node Functions

Each node receives the full state, does its work, and returns updated state:

```python
def risk_assessor_node(state: WealthAdvisorState) -> WealthAdvisorState:
    output = run_risk_assessment(
        portfolio_description=state["portfolio_data"],
        chat_history=state["messages"]
    )
    return {
        **state,                    # copy all existing fields
        "risk_output": output,      # update this field
        "messages": state["messages"] + [AIMessage(content=output)]
    }
```

### Routing

```python
# Supervisor decides which agent handles the request
def route_after_supervisor(state) -> Literal["risk_assessor", "financial_planner", "client_comms"]:
    return state["next_agent"]  # set by supervisor node

# After human review — approve or retry
def route_after_review(state) -> Literal["client_comms", "risk_assessor"]:
    return "client_comms" if state.get("human_approved") else "risk_assessor"
```

### Human-in-the-Loop

```python
# Inside human_review_node
human_decision = interrupt({
    "message": "Please review and approve.",
    "analysis": combined_analysis,
})
# Graph PAUSES here — state saved to MemorySaver
# Resumes when advisor calls resume_workflow()

approved = human_decision.get("approved", False)
feedback = human_decision.get("feedback", "")
```

---

## RAG Pipeline (Retrieval-Augmented Generation)

```
Step 1: FETCH
SEC EDGAR API → raw .txt file (HTML + XBRL)
        ↓
BeautifulSoup.get_text() → strips all tags
        ↓
text.find("ITEM 1.") → skip XBRL headers
        ↓
First 50,000 chars → readable content

Step 2: INDEX
chunk_text() → 63 chunks (1000 chars, 200 overlap)
        ↓
HuggingFace MiniLM.embed_documents() → 384-dim vectors
        ↓
ChromaDB.upsert(documents, embeddings, metadata)
        ↓
Stored: {ticker, form_type, filing_date, chunk_index}

Step 3: RETRIEVE
Agent question → MiniLM.embed_query() → 384-dim vector
        ↓
ChromaDB.query(query_embeddings, n_results=5)
        ↓
Cosine similarity → top 5 most relevant chunks
        ↓
Clean text with citations → agent generates insight
```

### Why 50,000 chars?

Full 10-K filings are 500,000+ characters. The first 50K covers:
- Item 1: Business overview
- Item 1A: Risk Factors (most valuable for risk assessment)
- Item 1B/1C: Cybersecurity disclosures

This captures the most important sections at 10x lower cost.

---

## Chat Agent Architecture

The chat interface uses a **lightweight agent** separate from the full analysis workflow:

```python
# Full analysis agent — 60 seconds, 5 tools, 15 iterations
AgentExecutor(tools=[get_stock_metrics, get_price_data, analyze_portfolio,
                     search_sec_filings, index_sec_filing], max_iterations=15)

# Chat agent — 5 seconds, 2 tools, 3 iterations
AgentExecutor(tools=[get_stock_metrics, get_price_data], max_iterations=3)
```

Chat agent receives:
1. System prompt with client profile + past sessions from SQLite
2. Full conversation history (converted to LangChain messages)
3. Current user question

This gives instant responses (2-5 seconds) while maintaining context.

---

## Topic Guardrails

Every chat message passes through a classifier before reaching the agent:

```python
def is_relevant_question(question: str, llm) -> bool:
    # Returns YES for:
    # - Stock/portfolio/finance questions
    # - Follow-up to previous messages
    # - Greetings
    # Returns NO for:
    # - Politics, sports, entertainment
    # - General knowledge questions
    # - Off-topic requests
```

If NO → agent responds: "I'm specialized in wealth management only."
If YES → chat agent processes the question with tools.

---

## Client Memory System

```
┌─────────────────────────────────────────────┐
│              SQLite Database                 │
│                                             │
│  client_profiles table                      │
│  ├── client_id (PRIMARY KEY)                │
│  ├── client_name                            │
│  ├── risk_tolerance                         │
│  ├── investment_goals                       │
│  ├── time_horizon                           │
│  ├── created_at                             │
│  └── updated_at                             │
│                                             │
│  analysis_sessions table                    │
│  ├── session_id (PRIMARY KEY)               │
│  ├── client_id (FOREIGN KEY)                │
│  ├── portfolio_data                         │
│  ├── risk_output                            │
│  ├── planning_output                        │
│  ├── client_summary                         │
│  ├── risk_score                             │
│  └── created_at                             │
└─────────────────────────────────────────────┘
```

**Flow:**
1. Client runs analysis → saved to `analysis_sessions`
2. Next session → `load_client_history()` fetches last 3 sessions
3. Injected into chat agent system prompt as context
4. Agent answers "What was my risk last time?" from SQLite

---

## Sequential vs Parallel (Current vs Future)

**Current (Sequential):**
```python
builder.add_edge("supervisor", "risk_assessor")
builder.add_edge("risk_assessor", "human_review")
# Risk and Planning run one at a time
```

**Future (Parallel) — only graph.py changes:**
```python
from langgraph.constants import Send

def parallel_dispatch(state):
    return [
        Send("risk_assessor", state),
        Send("financial_planner", state)  # runs simultaneously!
    ]

builder.add_conditional_edges("supervisor", parallel_dispatch)
```

The agents themselves don't change — only the graph edges. This will cut analysis time from 60s to ~30s.

---

## Security

- API keys in `.env` — never hardcoded
- `.env` in `.gitignore` — never committed to GitHub
- SEC EDGAR is public data — no privacy concerns
- ChromaDB is local — filing data never leaves your machine
- HuggingFace embeddings run locally — no data sent externally
- SQLite is local — client data stays on your server
- Topic guardrails — prevents misuse of the AI

---

## Performance Benchmarks

| Operation | Time |
|-----------|------|
| Fetch SEC filing | ~2-3 seconds |
| BeautifulSoup HTML cleaning | ~0.5 seconds |
| Index 63 chunks (local MiniLM) | ~5-8 seconds |
| Semantic search | ~0.1 seconds |
| Full Risk Assessor agent | ~30-45 seconds |
| Financial Planner agent | ~20-30 seconds |
| Client Comms (no tools) | ~3-5 seconds |
| Chat response (lightweight) | ~2-5 seconds |
| Human review | Human dependent |
| Total full workflow | ~60-90 seconds |
