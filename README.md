# 📈 WealthAdvisor AI Agent

> A production-grade, multi-agent AI system that automates wealth management workflows — from real-time portfolio risk assessment to SEC filing analysis and personalized client reporting.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1.0-green)
![Gemini](https://img.shields.io/badge/Gemini-3.1%20Pro-orange)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Latest-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🧠 What is WealthAdvisor AI?

WealthAdvisor AI is an intelligent, multi-agent system that works like a team of financial specialists — each with a specific role, working together to analyze portfolios, read SEC filings, run scenario analyses, and generate client-ready reports.

**The problem it solves:**

A human wealth advisor spends hours every week:
- Manually reading SEC filings (10-K, 10-Q) to find risk signals
- Running bull/base/bear scenario analyses in spreadsheets
- Writing personalized client summaries from raw data

WealthAdvisor AI automates all of this in minutes — not hours.

**Who is it for?**
- Wealth management firms looking to augment advisors with AI
- Financial analysts who want faster, data-driven insights
- Developers building AI-powered fintech products

---

## 🏗️ Architecture

```
User Input (Portfolio Holdings)
           │
           ▼
    ┌─────────────┐
    │  Supervisor  │  ← Understands intent, routes to right agent
    └──────┬──────┘
           │
    ┌──────┴────────────────────┐
    ▼                           ▼
┌─────────────────┐    ┌──────────────────────┐
│  Risk Assessor  │    │  Financial Planner   │
│                 │    │                      │
│ • Pulls SEC     │    │ • Bull case (+25%)   │
│   10-K / 10-Q  │    │ • Base case (~10%)   │
│ • Market data   │    │ • Bear case (-20%)   │
│ • Beta, PE,     │    │ • 1yr/3yr/5yr        │
│   sector risk   │    │   projections        │
│ • Risk scoring  │    │ • Rebalancing tips   │
└────────┬────────┘    └──────────┬───────────┘
         └──────────┬─────────────┘
                    ▼
         ┌──────────────────┐
         │  Human Review    │  ← Advisor approves or gives feedback
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │  Client Comms    │  ← Drafts plain-English client summary
         └──────────────────┘
                  ▼
         Final Report + Dashboard
```

### How the agents collaborate

1. **Supervisor** receives the user's portfolio and intent, decides which specialist should handle it
2. **Risk Assessor** pulls live market data and reads SEC filings via RAG (retrieval-augmented generation) to score portfolio risk
3. **Financial Planner** runs scenario analyses with real price data and projects future outcomes
4. **Human Review Gate** pauses execution — the advisor reviews and approves or gives feedback
5. **Client Comms** transforms all analysis into a clear, professional client-ready summary

---

## ⚙️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Agent Orchestration** | LangGraph 1.1.0 | Best-in-class for stateful, multi-agent financial workflows with human-in-the-loop |
| **LLM** | Gemini 3.1 Pro | 2M token context window — reads entire SEC filings; strong financial reasoning |
| **Vector Database** | ChromaDB | Local, fast semantic search over SEC filing chunks |
| **Embeddings** | Gemini Embedding 001 | High-quality financial text embeddings |
| **Market Data** | yfinance | Live stock prices, beta, PE ratios, sector data |
| **SEC Data** | SEC EDGAR API | Free, official source for all public company filings |
| **API** | FastAPI | Async, production-ready REST API |
| **Dashboard** | Streamlit + Plotly | Interactive portfolio visualization and agent output |
| **Evaluation** | RAGAS + LangSmith | Measures RAG quality: faithfulness, relevancy, recall |
| **Deployment** | Docker + docker-compose | One-command deployment |

---

## ✨ Features

### ✅ Built (Data Layer)
- **Live market data** — real-time stock prices, beta, PE ratios, sector allocation via yfinance
- **SEC EDGAR integration** — pulls real 10-K and 10-Q filings for any public company
- **Semantic search** — ChromaDB vector store with Gemini embeddings for intelligent filing search
- **Portfolio metrics** — weighted beta, sector concentration, multi-position analysis

### 🚧 In Progress (Agents)
- Multi-agent LangGraph workflow
- Risk scoring (LOW / MODERATE / HIGH / CRITICAL)
- Bull/Base/Bear scenario analysis
- Human-in-the-loop review gate
- Client summary generation

### 📋 Planned
- FastAPI REST endpoints
- Streamlit dashboard with Plotly charts
- RAGAS evaluation harness
- Docker deployment
- PDF report export

---

## 📁 Project Structure

```
wealthadvisor/
│
├── agents/                    # LangGraph agent definitions
│   ├── graph.py               # Main workflow orchestrator
│   ├── supervisor.py          # Routes requests to specialist agents
│   ├── risk_assessor.py       # Portfolio risk + SEC filing analysis
│   ├── financial_planner.py   # Scenario analysis (bull/base/bear)
│   └── client_comms.py        # Drafts personalized client summaries
│
├── data/                      # Data layer — fetching and storage
│   ├── market_data.py         # yfinance wrapper (prices, metrics)
│   ├── sec_fetcher.py         # SEC EDGAR API client
│   └── vector_store.py        # ChromaDB indexing and retrieval
│
├── tools/                     # LangChain tools for agents
│   └── portfolio_tools.py     # Tools agents can call (analyze, search, fetch)
│
├── api/                       # FastAPI backend
│   └── main.py                # REST endpoints (/analyze, /review)
│
├── ui/                        # Streamlit dashboard
│   └── dashboard.py           # Interactive portfolio UI
│
├── eval/                      # Evaluation harness
│   └── harness.py             # RAGAS + LangSmith evaluation
│
├── config/                    # Configuration
│   └── settings.py            # Pydantic settings (loads from .env)
│
├── tests/                     # Test suite
│   └── test_data_layer.py     # Data layer tests (all passing ✅)
│
├── .env.example               # Environment variable template
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Multi-service orchestration
└── README.md                  # You are here
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Gemini API key ([Get one free](https://aistudio.google.com/app/apikey))
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/wealthadvisor-ai.git
cd wealthadvisor-ai

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your Gemini API key
```

### Environment Variables

```env
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.1-pro-preview
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=wealthadvisor
APP_ENV=development
LOG_LEVEL=INFO
```

### Run Tests

```bash
python tests/test_data_layer.py
```

Expected output:
```
✅ test_get_key_metrics       PASSED
✅ test_get_price_history     PASSED
✅ test_calculate_portfolio_metrics  PASSED
✅ test_get_cik               PASSED
✅ test_get_recent_filings    PASSED
✅ test_fetch_filing_text     PASSED
✅ test_chunk_text            PASSED
✅ test_index_and_query       PASSED
✅ All tests passed!
```

### Run the API (coming soon)

```bash
uvicorn api.main:app --reload --port 8000
```

### Run the Dashboard (coming soon)

```bash
streamlit run ui/dashboard.py
```

### Run with Docker (coming soon)

```bash
docker-compose up --build
```

---

## 🔍 How It Works — Under the Hood

### 1. SEC Filing Analysis (RAG Pipeline)

```
Apple 10-K (200 pages)
       ↓
Split into 1000-char chunks with 200-char overlap
       ↓
Each chunk → Gemini Embedding (3072 dimensions)
       ↓
Stored in ChromaDB
       ↓
Agent asks: "What are Apple's risk factors?"
       ↓
ChromaDB finds top 5 most relevant chunks
       ↓
Agent reads only relevant context → generates insight
```

### 2. Portfolio Risk Scoring

The Risk Assessor agent combines:
- **Market data** → beta, volatility, sector concentration
- **SEC insights** → material risks from filings
- **Scoring model** → LOW / MODERATE / HIGH / CRITICAL

### 3. Human-in-the-Loop

LangGraph's interrupt mechanism pauses the workflow at the review gate. The advisor can:
- ✅ **Approve** → proceeds to client summary generation
- 🔁 **Give feedback** → agents regenerate with new context

---

## 📊 Data Sources

| Source | Data | Cost |
|--------|------|------|
| SEC EDGAR API | 10-K, 10-Q filings for all public companies | Free |
| Yahoo Finance (yfinance) | Stock prices, beta, PE, market cap | Free |
| Gemini API | LLM + embeddings | Free tier available |

---

## 🗺️ Roadmap

- [x] Data layer (market data, SEC fetcher, vector store)
- [ ] LangChain tools
- [ ] LangGraph multi-agent workflow
- [ ] FastAPI backend
- [ ] Streamlit dashboard
- [ ] RAGAS evaluation harness
- [ ] Docker deployment
- [ ] PDF report export
- [ ] GraphDB integration for company relationship mapping
- [ ] Real-time alerts (portfolio risk threshold notifications)

---

## 👨‍💻 Author

**Chakravarthi Boora**
Applied AI Technical Analyst · Generative & Agentic AI · Wealth & Financial AI

[GitHub](https://github.com)

---

## ⚠️ Disclaimer

This project is for educational and informational purposes only. It does not constitute financial advice. Always consult a qualified financial advisor before making investment decisions.

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
