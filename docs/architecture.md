# WealthAdvisor AI — Architecture Deep Dive

## Overview

WealthAdvisor AI is built on a **multi-agent architecture** using LangGraph. Instead of one large AI model trying to do everything, we use specialized agents — each an expert in one domain — coordinated by a supervisor.

This mirrors how a real wealth management firm works:
- A **relationship manager** (supervisor) understands the client's needs
- A **risk analyst** (risk assessor) digs into the numbers and filings
- A **financial planner** (financial planner) models future scenarios
- A **client advisor** (client comms) communicates findings clearly

---

## Current Stack (Updated June 2026)

| Layer | Technology | Notes |
|-------|-----------|-------|
| Agent Orchestration | LangGraph 1.1.0 | Sequential now, parallel in future |
| LLM | Groq + openai (openai/gpt-oss-120b) | Free, fast, optimized for tool calling |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | 100% local — no API quota |
| Vector DB | ChromaDB | Local persistent storage |
| Market Data | yfinance | Live prices, beta, sector data |
| SEC Data | SEC EDGAR API | Free government API |
| HTML Parsing | BeautifulSoup4 | Strips HTML from SEC filings |

---

## Why Groq instead of Gemini/OpenAI for LLM?

During development we discovered:
- **Gemini 3.1 Pro** → paid only (removed from free tier April 2026)
- **Gemini 2.5 Flash** → free but only 5 RPM — not enough for multi-tool agents
- **Groq** → free, 100+ RPM, specifically optimized for tool calling

Groq runs LLaMA 3 at extremely high speed (289 tokens/second) — perfect for agents that make multiple tool calls per request.

---

## Why HuggingFace embeddings instead of Gemini?

During development we hit Gemini embedding quota limits when indexing multiple SEC filings. HuggingFace `all-MiniLM-L6-v2`:
- Runs **100% locally** on your machine
- **No API calls** — no quota, no cost
- **384-dimension vectors** — fast and accurate for financial text
- Downloads once, cached forever

---

## Agent Workflow (LangGraph State Machine)

```
START
  │
  ▼
┌─────────────┐
│  Supervisor  │  ← Groq openai, temperature=0
│             │  ← Returns one of: risk_assessor,
│             │    financial_planner, client_comms
└──────┬──────┘
       │
       ├──────────────────────┬────────────────────────┐
       ▼                      ▼                        ▼
┌─────────────┐      ┌──────────────────┐    ┌──────────────┐
│    Risk     │      │    Financial     │    │   Client     │
│  Assessor  │      │    Planner       │    │   Comms      │
│  ✅ Built   │      │  🚧 In Progress  │    │  📋 Planned  │
└──────┬──────┘      └────────┬─────────┘    └──────┬───────┘
       │                      │                      │
       └──────────┬───────────┘                      │
                  ▼                                   │
        ┌──────────────────┐                          │
        │  Human Review    │                          │
        │  (Interrupt)     │                          │
        └────────┬─────────┘                          │
                 │                                    │
          approved?                                   │
           ├─ YES ──────────────────────────────────► │
           └─ NO → back to Risk Assessor              │
                                                      ▼
                                                    END
```

### State Object

Every node in the graph reads from and writes to a shared **state object**:

```python
class WealthAdvisorState(TypedDict):
    messages: list           # Full conversation history
    user_input: str          # Current user request
    portfolio_data: str      # Raw portfolio description
    risk_output: str         # Risk assessor writes here ✅
    planning_output: str     # Financial planner writes here
    client_summary: str      # Client comms writes here
    next_agent: str          # Supervisor routing decision
    human_approved: bool     # Human-in-the-loop gate
    client_name: str         # For personalization
```

Think of state as a **shared whiteboard** — each agent reads what previous agents wrote and adds their own output.

---

## Sequential vs Parallel (Current vs Future)

**Current (Sequential):**
```python
builder.add_edge("supervisor", "risk_assessor")
builder.add_edge("risk_assessor", "human_review")
```

**Future (Parallel) — only graph.py changes:**
```python
from langgraph.constants import Send

def parallel_dispatch(state):
    return [
        Send("risk_assessor", state),
        Send("financial_planner", state)  # runs simultaneously
    ]

builder.add_conditional_edges("supervisor", parallel_dispatch)
```

The agents themselves don't change — only how edges are connected in `graph.py`.

---

## Data Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Data Layer                        │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ market_data  │  │ sec_fetcher  │  │  vector   │  │
│  │    .py  ✅   │  │   .py  ✅    │  │ store.py✅│  │
│  │              │  │              │  │           │  │
│  │ • yfinance   │  │ • SEC EDGAR  │  │ • ChromaDB│  │
│  │ • Live prices│  │   API        │  │ • MiniLM  │  │
│  │ • Beta, PE   │  │ • 10-K, 10-Q │  │  embeddings│ │
│  │ • Market cap │  │ • BeautifulS │  │ • Semantic │  │
│  │ • Sector data│  │   oup clean  │  │   search  │  │
│  └──────────────┘  └──────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## RAG Pipeline (Updated)

```
Step 1: Ingest
──────────────
SEC Filing (raw .txt file from EDGAR)
        │
        ▼
BeautifulSoup → strips all HTML/XML tags
        │
        ▼
Skip to "ITEM 1." → jumps past XBRL headers
        │
        ▼
chunk_text() → 63 chunks of 1000 chars each
        │
        ▼
HuggingFace MiniLM → embed locally (384 dimensions)
        │
        ▼
ChromaDB.upsert() → stored with metadata


Step 2: Retrieve
────────────────
Agent question: "What are Apple's main risk factors?"
        │
        ▼
HuggingFace MiniLM → embed query (384 dimensions)
        │
        ▼
ChromaDB.query() → cosine similarity search
        │
        ▼
Top 5 most relevant clean text chunks returned


Step 3: Generate
────────────────
Relevant chunks + Agent system prompt
        │
        ▼
Groq openai (tool-use optimized)
        │
        ▼
Risk analysis with specific citations from SEC filing
```

---

## Risk Assessor Agent — Sample Output

The Risk Assessor produces structured reports like this:

```
## Portfolio Risk Assessment

### 1. Portfolio Overview
| Ticker | Weight | Beta | Sector    |
|--------|--------|------|-----------|
| AAPL   | 40%    | 1.09 | Technology|
| MSFT   | 60%    | 1.10 | Technology|

### 2. Risk Metrics
- Weighted Beta: 1.10
- Sector Concentration: 100% Technology
- 1-Year Return: +15.5%

### 3. SEC Insights
- Apple: Design/manufacturing defect risks
- Microsoft: OEM device-mix dependency

### 4. Risk Score: HIGH

### 5. Top 3 Risk Factors
1. Technology sector concentration (100%)
2. Apple supply chain exposure
3. Microsoft OEM revenue sensitivity
```

---

## Human-in-the-Loop Design

LangGraph's `interrupt` mechanism pauses at review gate:

```python
human_decision = interrupt({
    "message": "Please review the analysis and approve.",
    "analysis": combined_analysis,
})
approved = human_decision.get("approved", False)
feedback = human_decision.get("feedback", "")
```

- **Approve** → workflow continues to client summary
- **Reject with feedback** → agents regenerate
- State is checkpointed at every step using `MemorySaver`

---

## Security Considerations

- API keys loaded from `.env` (never hardcoded)
- `.env` in `.gitignore` (never committed)
- SEC EDGAR data is public — no privacy concerns
- ChromaDB is local — filing data never leaves your machine
- HuggingFace embeddings run locally — no data sent to external APIs

---

## Performance

| Operation | Time |
|-----------|------|
| Fetch SEC filing | ~2-3 seconds |
| Clean HTML with BeautifulSoup | ~0.5 seconds |
| Index 63 chunks with MiniLM | ~5-8 seconds (local) |
| Semantic search query | ~0.1 seconds (local) |
| Full Risk Assessor agent | ~30-45 seconds |
| Human review | Human dependent |
