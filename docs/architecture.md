# WealthAdvisor AI — Architecture Deep Dive

## Overview

WealthAdvisor AI is built on a **multi-agent architecture** using LangGraph. Instead of one large AI model trying to do everything, we use specialized agents — each an expert in one domain — coordinated by a supervisor.

This mirrors how a real wealth management firm works:
- A **relationship manager** (supervisor) understands the client's needs
- A **risk analyst** (risk assessor) digs into the numbers and filings
- A **financial planner** (financial planner) models future scenarios
- A **client advisor** (client comms) communicates findings clearly

---

## Agent Workflow (LangGraph State Machine)

```
START
  │
  ▼
┌─────────────┐
│  Supervisor  │
│             │
│ Reads user  │
│ intent and  │
│ routes to   │
│ right agent │
└──────┬──────┘
       │
       ├──────────────────────┬────────────────────────┐
       ▼                      ▼                        ▼
┌─────────────┐      ┌──────────────────┐    ┌──────────────┐
│    Risk     │      │    Financial     │    │   Client     │
│  Assessor  │      │    Planner       │    │   Comms      │
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
    risk_output: str         # Risk assessor output
    planning_output: str     # Financial planner output
    client_summary: str      # Final client communication
    next_agent: str          # Supervisor routing decision
    human_approved: bool     # Human-in-the-loop gate
    client_name: str         # For personalization
```

This state is **persisted** using LangGraph's `MemorySaver` — so if the workflow is interrupted (human review), it can resume exactly where it left off.

---

## Data Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Data Layer                        │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ market_data  │  │ sec_fetcher  │  │  vector   │  │
│  │    .py       │  │    .py       │  │  store.py │  │
│  │              │  │              │  │           │  │
│  │ • yfinance   │  │ • SEC EDGAR  │  │ • ChromaDB│  │
│  │ • Live prices│  │   API        │  │ • Gemini  │  │
│  │ • Beta, PE   │  │ • 10-K, 10-Q │  │  embeddings│ │
│  │ • Market cap │  │ • CIK lookup │  │ • Semantic │  │
│  │ • Sector data│  │ • Filing text│  │   search  │  │
│  └──────────────┘  └──────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────┘
```

### market_data.py

Wraps Yahoo Finance (yfinance) to provide:

| Function | Input | Output |
|----------|-------|--------|
| `get_key_metrics(ticker)` | "AAPL" | PE, beta, market cap, price |
| `get_price_history(ticker, period)` | "AAPL", "1y" | DataFrame of OHLCV data |
| `calculate_portfolio_metrics(holdings)` | List of holdings | Portfolio-level metrics |

### sec_fetcher.py

Interfaces with SEC EDGAR's free API:

| Function | Input | Output |
|----------|-------|--------|
| `get_cik(ticker)` | "AAPL" | "0000320193" |
| `get_recent_filings(ticker, form_type, count)` | "AAPL", "10-K", 3 | List of filing metadata |
| `fetch_filing_text(accession_number, ticker)` | "0000320193-25-000079", "AAPL" | Raw filing text (50K chars) |

### vector_store.py

Manages ChromaDB for semantic search:

| Function | Input | Output |
|----------|-------|--------|
| `chunk_text(text)` | Long string | List of 1000-char chunks |
| `get_embeddings()` | — | Gemini embedding model |
| `get_collection()` | — | ChromaDB collection |
| `index_document(text, doc_id, metadata)` | Filing text | Number of chunks indexed |
| `query(query_text, n_results)` | Question string | Top N relevant chunks |

---

## RAG Pipeline (Retrieval-Augmented Generation)

This is how the Risk Assessor reads SEC filings intelligently:

```
Step 1: Ingest
──────────────
SEC Filing (50,000 chars)
        │
        ▼
chunk_text() → 63 chunks of 1000 chars each
        │
        ▼
get_embeddings().embed_documents() → 63 vectors of 3072 dimensions
        │
        ▼
ChromaDB.upsert() → stored with metadata {ticker, form_type, date}


Step 2: Retrieve
────────────────
Agent question: "What are Apple's main risk factors?"
        │
        ▼
get_embeddings().embed_query() → 1 vector of 3072 dimensions
        │
        ▼
ChromaDB.query() → cosine similarity search
        │
        ▼
Top 5 most relevant chunks returned


Step 3: Generate
────────────────
Relevant chunks + Agent system prompt
        │
        ▼
Gemini 3.1 Pro
        │
        ▼
Risk analysis with specific citations from SEC filing
```

**Why RAG instead of just sending the whole filing?**

| Approach | Tokens used | Cost | Speed |
|----------|------------|------|-------|
| Send full 10-K | ~100,000 tokens | High | Slow |
| RAG (top 5 chunks) | ~5,000 tokens | 20x cheaper | Fast |

---

## Human-in-the-Loop Design

LangGraph's `interrupt` mechanism is used at the review gate:

```python
# Execution PAUSES here
human_decision = interrupt({
    "message": "Please review the analysis and approve.",
    "analysis": combined_analysis,
})

# Execution RESUMES when advisor responds
approved = human_decision.get("approved", False)
feedback = human_decision.get("feedback", "")
```

This gives advisors full control:
- **Approve** → workflow continues to client summary
- **Reject with feedback** → agents regenerate with new context
- **Edit** → advisor can modify the analysis before it reaches the client

The state is checkpointed at every step using `MemorySaver`, so nothing is lost during the pause.

---

## Security Considerations

- API keys are loaded from `.env` (never hardcoded)
- `.env` is in `.gitignore` (never committed to GitHub)
- SEC EDGAR data is public — no data privacy concerns
- No user financial data is stored permanently
- ChromaDB is local — filing data never leaves your machine

---

## Performance

| Operation | Time |
|-----------|------|
| Fetch SEC filing | ~2-3 seconds |
| Index 63 chunks with embeddings | ~10-15 seconds |
| Semantic search query | ~0.5 seconds |
| Full agent workflow | ~30-60 seconds |
| Human review (variable) | Human dependent |
