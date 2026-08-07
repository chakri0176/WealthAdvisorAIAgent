# Agent System Documentation

WealthAdvisor AI uses four specialist agents coordinated by LangGraph. Each agent is an expert in one domain.

---

## Overview

```
User Request
     │
     ▼
┌─────────────┐
│  Supervisor │  → reads intent, routes to right agent
└──────┬──────┘
       │
  ┌────┼────────────┐
  ▼    ▼            ▼
Risk  Financial  Client
Assessor Planner  Comms
  │    │
  └────┘
     │
     ▼
Human Review Gate
     │
     ▼
Client Comms → Final Summary
```

---

## 1. Supervisor Agent

**File:** `agents/supervisor.py`
**Model:** Groq LLaMA 3.3 70B (temperature=0)
**Tools:** None — pure routing logic

### What it does

Reads the user's request and returns exactly one word:
- `risk_assessor`
- `financial_planner`
- `client_comms`

### Routing Logic

| User says... | Routes to |
|-------------|-----------|
| "Analyze my portfolio risk" | risk_assessor |
| "What's my biggest risk?" | risk_assessor |
| "Show me SEC filing risks" | risk_assessor |
| "Run bull/bear scenarios" | financial_planner |
| "Project my portfolio value" | financial_planner |
| "Draft a client summary" | client_comms |
| "Write a report for my client" | client_comms |
| Unclear request | risk_assessor (default) |

### Why temperature=0?

Routing decisions must be **deterministic**. We always want the same question to route to the same agent. Temperature=0 eliminates randomness.

### Code Pattern

```python
def route_request(user_message: str) -> str:
    llm = ChatGroq(model=settings.groq_model, temperature=0)
    messages = [
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=user_message)
    ]
    response = llm.invoke(messages)
    agent_name = response.content.strip().lower()
    valid = {"risk_assessor", "financial_planner", "client_comms"}
    return agent_name if agent_name in valid else "risk_assessor"
```

---

## 2. Risk Assessor Agent

**File:** `agents/risk_assessor.py`
**Model:** Groq LLaMA 3.3 70B (temperature=0)
**Tools:** All 5 tools
**Max iterations:** 15

### What it does

Produces a comprehensive risk report by:
1. Calling `analyze_portfolio` → overall portfolio metrics
2. Calling `get_stock_metrics` for each ticker → beta, PE, sector
3. Calling `index_sec_filing` for each ticker → downloads and indexes 10-K
4. Calling `search_sec_filings` → finds real risk factors from filings
5. Calling `get_price_data` → 1yr returns and volatility

### Output Structure

```markdown
## Portfolio Risk Assessment — [Date]

### 1. Portfolio Overview
| Ticker | Weight | Beta | Sector | Current Price |
...

### 2. Risk Metrics
| Metric | Value |
| Weighted Beta | 1.10 |
| Sector Concentration | 75% Technology |
| Volatility | 48% |

### 3. SEC Insights
Apple (2025 10-K): design defects, supply chain...
Microsoft (2025 10-K): regulatory, OEM dependency...

### 4. Risk Score: MODERATE/HIGH/LOW/CRITICAL

### 5. Top 3 Risk Factors
1. Technology sector concentration (data-driven)
2. Apple supply chain exposure (from 10-K Item 1A)
3. Microsoft regulatory risk (EU Digital Markets Act)
```

### Risk Scoring

| Score | Criteria |
|-------|---------|
| LOW | Beta < 0.8, diversified sectors, no major SEC red flags |
| MODERATE | Beta 0.8-1.2, some concentration, manageable risks |
| HIGH | Beta > 1.2, concentrated sector, material SEC risk factors |
| CRITICAL | Beta > 1.5, extreme concentration, major regulatory/legal risks |

### Why 15 max_iterations?

For a 3-stock portfolio the agent needs:
- 1 analyze_portfolio call
- 3 get_stock_metrics calls
- 3 index_sec_filing calls
- 2-3 search_sec_filings calls
- 3 get_price_data calls
= ~13 tool calls + reasoning = ~15 iterations

---

## 3. Financial Planner Agent

**File:** `agents/financial_planner.py`
**Model:** Groq LLaMA 3.3 70B (temperature=0.2)
**Tools:** 3 tools (no SEC tools — keeps it fast)
**Max iterations:** 8

### What it does

Runs three market scenarios using real beta values from live market data:

**Bear Case (-20% market):**
```
Expected move per stock = Beta × (-20%)
AAPL: 1.086 × -20% = -21.72%
MSFT: 1.103 × -20% = -22.06%
```

**Base Case (+10% annual):**
```
Compound growth: V × (1.10)^t
1yr: $51,567 × 1.10 = $56,724
3yr: $51,567 × 1.331 = $68,639
5yr: $51,567 × 1.611 = $83,080
```

**Bull Case (+25% market):**
```
Expected move = Beta × (+25%)
AAPL: 1.086 × 25% = +27.15%
MSFT: 1.103 × 25% = +27.58%
Upside capture = (portfolio gain%) / (market gain%)
```

### Why temperature=0.2?

Slightly higher than 0 to allow natural language variation in the scenario descriptions. The math is deterministic but the explanation can vary.

### Rebalancing Logic

If any single holding exceeds 40% actual weight:
```
Target AAPL value = 0.40 × (AAPL + MSFT values)
Shares to sell = (Current value - Target value) / Current price
```

---

## 4. Client Communications Agent

**File:** `agents/client_comms.py`
**Model:** Groq LLaMA 3.3 70B (temperature=0.4)
**Tools:** None — pure writing
**Type:** Single LLM call (no AgentExecutor)

### What it does

Transforms raw analysis output into a professional client letter. No tools needed — just reading and writing.

### Output Structure

```
GREETING
Dear [Client Name],
I hope you are doing well...

EXECUTIVE SUMMARY
2-3 sentences on the most important finding.

KEY FINDINGS
• Portfolio risk score: MODERATE
• Weighted beta: 1.10
• 5-year base case projection: $83,080

WHAT THIS MEANS FOR YOU
Plain English explanation of impact on the client.

RECOMMENDED NEXT STEPS
1. Consider selling ~55 AAPL shares to rebalance
2. Add non-technology holdings for diversification
3. Review quarterly as market conditions change

CLOSING
Professional sign-off.

DISCLAIMER
"This analysis is for informational purposes only..."
```

### Why temperature=0.4?

Higher temperature makes the writing feel more natural and less robotic. The content (numbers, risk scores) comes from the analysis — the temperature only affects the language style.

### Code Pattern

```python
def draft_client_summary(analysis_text, client_name, tone) -> str:
    llm = ChatGroq(model=settings.groq_model, temperature=0.4)
    messages = [
        SystemMessage(content=CLIENT_COMMS_PROMPT),
        HumanMessage(content=f"Draft for {client_name}:\n{analysis_text}")
    ]
    response = llm.invoke(messages)
    return response.content
```

---

## 5. Chat Agent (Lightweight)

**File:** `ui/dashboard.py`
**Model:** Groq GPT-OSS 120B (temperature=0.3)
**Tools:** 2 tools (get_stock_metrics, get_price_data)
**Max iterations:** 3

### What it does

Handles quick conversational questions in the chat interface without running the full 60-second workflow.

### Context it receives

```python
SystemMessage(content=f"""
You are WealthAdvisor AI...
Client: {client_name}
Current portfolio: {json.dumps(holdings)}
Latest analysis: {risk_output[:500]}

PREVIOUS SESSIONS (from SQLite):
- 2026-07-01: Risk Score MODERATE | Summary: ...
- 2026-06-15: Risk Score HIGH | Summary: ...
Total past sessions: 5
""")
```

### Topic Guardrails

Every message passes through `is_relevant_question()` before reaching the agent:

```
Finance/wealth question → YES → chat agent processes it
General question        → NO  → "I only answer finance questions"
Follow-up question      → YES → chat agent processes it
Greeting               → YES → chat agent responds
```

---

## Agent Comparison

| | Supervisor | Risk Assessor | Financial Planner | Client Comms | Chat Agent |
|---|---|---|---|---|---|
| Tools | 0 | 5 | 3 | 0 | 2 |
| Max iterations | 1 | 15 | 8 | 1 | 3 |
| Temperature | 0 | 0 | 0.2 | 0.4 | 0.3 |
| Time | <1s | 30-45s | 20-30s | 3-5s | 2-5s |
| Purpose | Route | Analyze risk | Model scenarios | Write letter | Quick answers |

---

## Tool Reference

| Tool | Function | Used By |
|------|---------|---------|
| `get_stock_metrics` | PE, beta, market cap, sector | Risk, Planner, Chat |
| `get_price_data` | 1yr history, returns, high/low | Risk, Planner, Chat |
| `analyze_portfolio` | Portfolio-level metrics | Risk, Planner |
| `index_sec_filing` | Download + embed 10-K | Risk |
| `search_sec_filings` | Semantic search over filings | Risk |

---

## Test Results

```bash
python tests/test_agents.py
```

```
✅ test_supervisor        risk_assessor / financial_planner / client_comms
✅ test_client_comms      Professional letter generated for John Smith
✅ test_risk_assessor     Full risk report with SEC citations
✅ test_financial_planner Bear/base/bull scenarios with exact math
✅ All 4 agent tests passed!
```

---

## Future Agent Plans

### Phase 2 — Alert Agent
Monitors portfolio daily and sends alerts when:
- Risk score changes (MODERATE → HIGH)
- Any holding drops > 10% in a day
- New SEC filing detected for a holding

### Phase 3 — Research Agent
Deep-dives into specific companies:
- Reads multiple filings (10-K + 10-Q + 8-K)
- Compares competitor SEC filings
- Generates industry analysis reports

### Phase 4 — Parallel Execution
Risk Assessor and Financial Planner run simultaneously:
```python
# LangGraph Send API for parallel execution
def parallel_dispatch(state):
    return [
        Send("risk_assessor", state),
        Send("financial_planner", state)
    ]
```
Cuts total analysis time from 60s to ~35s.
