# 📈 WealthAdvisor AI Agent

> A production-grade, multi-agent AI system that automates wealth management workflows — from real-time portfolio risk assessment to SEC filing analysis, scenario planning, and personalized client reporting.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1.0-green)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-orange)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5.23-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)
![License](https://img.shields.io/badge/License-Proprietary-red)

---

## 🧠 What is WealthAdvisor AI?

WealthAdvisor AI is an intelligent, multi-agent system that works like a team of financial specialists — each with a specific role, working together to analyze portfolios, read SEC filings, run scenario analyses, and generate client-ready reports.

**The problem it solves:**

A human wealth advisor spends hours every week:
- Manually reading SEC filings (10-K, 10-Q) to find risk signals
- Running bull/base/bear scenario analyses in spreadsheets
- Writing personalized client summaries from raw data
- Tracking client history across multiple sessions

WealthAdvisor AI automates all of this — in minutes, not hours.

**Who is it for?**
- Independent financial advisors (RIAs) looking to scale their practice
- Small wealth management firms who can't afford Bloomberg Terminal ($25K/year)
- Individual investors wanting professional-grade analysis
- Fintech developers building AI-powered financial products

---

## 🏗️ Architecture

```
User Input (Portfolio Holdings)
           │
           ▼
    ┌─────────────┐
    │  Supervisor  │  ← Routes to the right specialist agent
    └──────┬──────┘
           │
    ┌──────┴────────────────────┐
    ▼                           ▼
┌─────────────────┐    ┌──────────────────────┐
│  Risk Assessor  │    │  Financial Planner   │
│                 │    │                      │
│ • Live market   │    │ • Bull case (+25%)   │
│   data (beta,   │    │ • Base case (~10%)   │
│   PE, sector)   │    │ • Bear case (-20%)   │
│ • SEC 10-K/10-Q │    │ • 1yr/3yr/5yr        │
│   filing RAG    │    │   projections        │
│ • Risk scoring  │    │ • Rebalancing tips   │
└────────┬────────┘    └──────────┬───────────┘
         └──────────┬─────────────┘
                    ▼
         ┌──────────────────┐
         │  Human Review    │  ← Advisor approves or gives feedback
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │  Client Comms    │  ← Drafts professional client summary
         └──────────────────┘
                  ▼
    Chat Interface + Client Memory
```

---

## ⚙️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Agent Orchestration** | LangGraph 1.1.0 | Stateful multi-agent workflows with human-in-the-loop |
| **LLM (Analysis)** | Groq + LLaMA 3.3 70B | Free, fast, optimized for tool calling |
| **LLM (Chat)** | Groq + GPT-OSS 120B | High capability for financial reasoning |
| **Embeddings** | HuggingFace all-MiniLM-L6-v2 | 100% local — no API quota, no cost |
| **Vector Database** | ChromaDB 0.5.23 | Local semantic search over SEC filings |
| **Market Data** | yfinance | Live stock prices, beta, PE ratios |
| **SEC Data** | SEC EDGAR API | Free official US government filing database |
| **HTML Parsing** | BeautifulSoup4 | Cleans SEC filing HTML before indexing |
| **Client Memory** | SQLite | Persistent client profiles and session history |
| **API** | FastAPI 0.115 | Async REST API backend |
| **Dashboard** | Streamlit 1.35 + Plotly | Interactive chat + portfolio visualization |
| **Deployment** | Render + Streamlit Cloud | Free tier deployment |

---

## ✨ Features

### ✅ Completed

**Data Layer**
- Live market data — real-time stock prices, beta, PE ratios, sector allocation
- SEC EDGAR integration — real 10-K and 10-Q filings for any US public company
- HTML cleaning — BeautifulSoup strips markup for clean, readable filing text
- Semantic search — ChromaDB with local HuggingFace embeddings

**AI Agents**
- Supervisor agent — routes requests to the right specialist
- Risk Assessor — full risk report with SEC citations and risk scoring (LOW/MODERATE/HIGH/CRITICAL)
- Financial Planner — bull/base/bear scenarios with 1yr/3yr/5yr projections
- Client Comms — professional client letters with greeting, findings, next steps

**5 LangChain Tools**
- `get_stock_metrics` — live PE, beta, market cap
- `get_price_data` — 1yr price history and returns
- `analyze_portfolio` — full portfolio metrics
- `index_sec_filing` — downloads and indexes company 10-K
- `search_sec_filings` — semantic search over indexed filings

**LangGraph Workflow**
- Human-in-the-loop review gate — advisor approves before client sees output
- State persistence with MemorySaver — workflow pauses and resumes correctly
- Thread-based session management — multiple clients simultaneously

**Chat Interface**
- Natural language chat with AI agents
- Topic guardrails — only answers finance/wealth questions
- Full conversation memory within session
- Live stock price lookup in chat

**Client Memory (SQLite)**
- Persistent client profiles across sessions
- Full analysis history per client
- Agent reads past sessions automatically
- "What was my risk score last time?" — answered correctly

**API & Dashboard**
- FastAPI backend with `/health`, `/analyze`, `/review` endpoints
- Auto-generated Swagger UI docs
- Streamlit dashboard with portfolio pie chart
- Download client summary as .txt file

### 🚧 In Progress
- Render + Streamlit Cloud deployment
- Docker containerization

### 📋 Planned (Future)
- PDF report export with professional formatting
- Email client summary directly from dashboard
- Portfolio comparison charts over time
- Real-time alerts (risk score changes, price thresholds)
- Multi-user authentication (JWT)
- Stripe payment integration
- White-label version for wealth management firms
- Indian/UK/EU stock support (NSE, LSE, Euronext)
- GraphDB for company relationship mapping
- Automated quarterly re-analysis scheduler
- Bloomberg API integration (for enterprise tier)

---

## 📁 Project Structure

```
wealthadvisor/
│
├── agents/                      # LangGraph agent definitions
│   ├── graph.py                 # ✅ Main LangGraph workflow orchestrator
│   ├── supervisor.py            # ✅ Routes requests to specialist agents
│   ├── risk_assessor.py         # ✅ Portfolio risk + SEC filing analysis
│   ├── financial_planner.py     # ✅ Bull/base/bear scenario analysis
│   └── client_comms.py          # ✅ Professional client summary generation
│
├── data/                        # Data layer
│   ├── market_data.py           # ✅ yfinance wrapper (live prices, metrics)
│   ├── sec_fetcher.py           # ✅ SEC EDGAR API + BeautifulSoup cleaning
│   └── vector_store.py          # ✅ ChromaDB + HuggingFace embeddings
│
├── tools/                       # LangChain tools for agents
│   └── portfolio_tools.py       # ✅ 5 tools agents can call
│
├── clients/                     # Client memory system
│   ├── client_memory.py         # ✅ SQLite CRUD operations
│   └── wealthadvisor.db         # ✅ Auto-generated SQLite database
│
├── api/                         # FastAPI backend
│   └── main.py                  # ✅ REST endpoints (/analyze, /review, /health)
│
├── ui/                          # Streamlit dashboard
│   └── dashboard.py             # ✅ Chat interface + portfolio visualization
│
├── config/                      # Configuration
│   └── settings.py              # ✅ Pydantic settings (loads from .env)
│
├── tests/                       # Test suite
│   ├── test_data_layer.py       # ✅ 8 tests — all passing
│   ├── test_tools.py            # ✅ 7 tests — all passing
│   ├── test_agents.py           # ✅ 4 tests — all passing
│   ├── test_graph.py            # ✅ 1 end-to-end test — passing
│   └── test_client_memory.py    # ✅ 7 tests — all passing
│
├── docs/                        # Documentation
│   ├── architecture.md          # Technical deep dive
│   ├── data_layer.md            # Data layer explained
│   ├── agents.md                # Agent system explained
│   └── deployment.md            # Deployment guide
│
├── .env.example                 # Environment variable template
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Multi-service orchestration
├── render.yaml                  # Render deployment config
└── README.md                    # You are here
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Groq API key ([Free at console.groq.com](https://console.groq.com))
- Gemini API key ([Free at aistudio.google.com](https://aistudio.google.com/app/apikey))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/chakri0176/wealthadvisor-ai.git
cd wealthadvisor-ai

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Environment Variables

```env
# LLM — Groq (free and fast)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# Embeddings — Gemini (free tier)
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# App
APP_ENV=development
LOG_LEVEL=INFO
```

### Run Locally

```bash
# Terminal 1 — Start API
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Start Dashboard
streamlit run ui/dashboard.py
```

Open: **http://localhost:8501**

### Run Tests

```bash
python tests/test_data_layer.py
python tests/test_tools.py
python tests/test_agents.py
python tests/test_graph.py
python tests/test_client_memory.py
```

---

## 🔍 How It Works

### RAG Pipeline for SEC Filings

```
SEC 10-K Filing (200 pages raw HTML)
        ↓
BeautifulSoup strips all HTML tags
        ↓
Skip XBRL headers → jump to "ITEM 1."
        ↓
Split into 63 chunks (1000 chars, 200 overlap)
        ↓
HuggingFace MiniLM embeds locally (384 dimensions)
        ↓
ChromaDB stores with metadata {ticker, form_type, date}
        ↓
Agent searches: "What are Apple's risk factors?"
        ↓
ChromaDB returns top 5 most relevant chunks
        ↓
Agent generates insight with SEC citations
```

### Human-in-the-Loop

```python
# LangGraph pauses here automatically
human_decision = interrupt({
    "message": "Please review and approve.",
    "analysis": combined_analysis,
})
# Resumes when advisor clicks Approve
approved = human_decision.get("approved", False)
```

### Client Memory

```
Every analysis session → saved to SQLite
Next session → loaded automatically
Agent context includes:
  "Previous sessions: MODERATE (July 1), HIGH (June 15)..."
Client asks: "What was my risk last time?"
Agent answers: "Your risk score on July 1 was MODERATE"
```

---

## 📊 Sample Output

### Risk Assessment
```
Portfolio Risk Assessment — July 2026

Holdings: AAPL (40%), MSFT (35%), GOOGL (25%)
Weighted Beta: 1.096
Sector Concentration: Technology 75%, Comm Services 25%
Risk Score: MODERATE

Top 3 Risk Factors:
1. Technology sector concentration (75%)
2. Apple supply chain exposure (from 2025 10-K)
3. Microsoft regulatory risks (EU Digital Markets Act)
```

### Scenario Analysis
```
Bear Case (-20%): Portfolio drops to $40,295
Base Case (+10%): 1yr $56,724 → 3yr $68,639 → 5yr $83,080
Bull Case (+25%): Portfolio rises to $65,685 (109.6% capture)

Recommendation: Sell 55 AAPL shares to rebalance to 40%
```

---

## 💰 What Makes This Different from ChatGPT/Claude/Gemini

| Feature | ChatGPT/Claude | WealthAdvisor AI |
|---------|---------------|------------------|
| Live stock prices | ❌ Training data | ✅ Real-time yfinance |
| Real SEC filings | ❌ General knowledge | ✅ Official EDGAR API |
| Client memory | ❌ Starts fresh | ✅ SQLite history |
| Human review gate | ❌ No oversight | ✅ Compliance-friendly |
| Audit trail | ❌ Black box | ✅ Full reasoning trace |
| Financial workflow | ❌ Generic chat | ✅ Structured workflow |
| Cost vs Bloomberg | $25,000/year | $0 (open source) |

---

## 📊 Data Sources

| Source | Data | Cost |
|--------|------|------|
| SEC EDGAR API | 10-K, 10-Q filings — all US public companies | Free |
| Yahoo Finance (yfinance) | Live prices, beta, PE, market cap | Free |
| HuggingFace MiniLM | Local embeddings (runs on your machine) | Free |
| Groq API | LLM inference (LLaMA 3) | Free tier |
| SQLite | Client memory and session history | Free |

**Total running cost for development: $0**

---

## 🗺️ Roadmap

### Phase 1 — Core Product ✅ Complete
- [x] Data layer (market data, SEC fetcher, vector store)
- [x] HTML cleaning with BeautifulSoup
- [x] 5 LangChain tools
- [x] 4 AI agents (supervisor, risk, planner, comms)
- [x] LangGraph workflow with human-in-the-loop
- [x] FastAPI backend
- [x] Streamlit chat dashboard
- [x] Topic guardrails
- [x] Client memory (SQLite)
- [x] 27 tests — all passing

### Phase 2 — Deployment 🚧 In Progress
- [ ] Render deployment (FastAPI)
- [ ] Streamlit Cloud deployment (Dashboard)
- [ ] Custom domain
- [ ] Production environment variables

### Phase 3 — Product Polish 📋 Planned
- [ ] PDF report export
- [ ] Email client summary
- [ ] Portfolio history charts
- [ ] Real-time price alerts
- [ ] Multi-user authentication

### Phase 4 — Monetization 📋 Planned
- [ ] Stripe payment integration
- [ ] Free/Pro/Enterprise tiers
- [ ] White-label version
- [ ] API access for developers

### Phase 5 — Scale 📋 Future
- [ ] International stocks (NSE, LSE)
- [ ] GraphDB company relationships
- [ ] Automated quarterly re-analysis
- [ ] Bloomberg API integration
- [ ] Mobile app

---

## 👨‍💻 Author

**Chakravarthi Boora**
Applied AI Engineer · LangGraph · Multi-Agent Systems · Financial AI

[LinkedIn](https://linkedin.com) · [GitHub](https://github.com/chakri0176)

---

## ⚠️ Disclaimer

This project is for educational and informational purposes only. It does not constitute financial advice. Always consult a qualified financial advisor before making investment decisions. Past performance is not indicative of future results.

---

## 📄 License

This project uses a **proprietary license** — not open source.

| Use Case | Permission |
|----------|-----------|
| Personal learning and study | ✅ Free |
| Running locally for personal use | ✅ Free |
| Educational and research purposes | ✅ Free |
| Contributing via pull requests | ✅ Free |
| Commercial products or services | ❌ Contact required |
| SaaS deployment for paying users | ❌ Contact required |
| White-labeling or reselling | ❌ Contact required |
| Client work or consulting | ❌ Contact required |

**To request commercial use permission:**

📧 chakravarthi.b167@gmail.com
🐙 [github.com/chakri0176](https://github.com/chakri0176)

See [LICENSE](./LICENSE) for full terms.
