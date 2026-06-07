# 📈 WealthAdvisor AI Agent

> A production-grade, multi-agent AI system that automates wealth management workflows — from real-time portfolio risk assessment to SEC filing analysis and personalized client reporting.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1.0-green)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-orange)
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
2. **Risk Assessor** pulls live market data and reads SEC filings via RAG to score portfolio risk
3. **Financial Planner** runs scenario analyses with real price data and projects future outcomes
4. **Human Review Gate** pauses execution — the advisor reviews and approves or gives feedback
5. **Client Comms** transforms all analysis into a clear, professional client-ready summary

---

## ⚙️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Agent Orchestration** | LangGraph 1.1.0 | Best-in-class for stateful, multi-agent financial workflows with human-in-the-loop |
| **LLM** | Groq + openai (openai/gpt-oss-120b) | Free, extremely fast, optimized for tool calling |
| **Vector Database** | ChromaDB | Local, fast semantic search over SEC filing chunks |
| **Embeddings** | HuggingFace all-MiniLM-L6-v2 | Runs 100% locally — no API quota, no cost |
| **Market Data** | yfinance | Live stock prices, beta, PE ratios, sector data |
| **SEC Data** | SEC EDGAR API | Free, official source for all public company filings |
| **HTML Parsing** | BeautifulSoup4 | Cleans SEC filing HTML before indexing |
| **API** | FastAPI | Async, production-ready REST API |
| **Dashboard** | Streamlit + Plotly | Interactive portfolio visualization and agent output |
| **Evaluation** | RAGAS + LangSmith | Measures RAG quality: faithfulness, relevancy, recall |
| **Deployment** | Docker + docker-compose | One-command deployment |

---

## ✨ Features

### ✅ Built (Data Layer + Agents)
- **Live market data** — real-time stock prices, beta, PE ratios, sector allocation via yfinance
- **SEC EDGAR integration** — pulls real 10-K and 10-Q filings for any public company
- **HTML cleaning** — BeautifulSoup strips markup before indexing for clean readable text
- **Semantic search** — ChromaDB vector store with local HuggingFace embeddings
- **Portfolio metrics** — weighted beta, sector concentration, multi-position analysis
- **Supervisor agent** — routes requests to the right specialist agent
- **Risk Assessor agent** — produces full risk reports with SEC citations and risk scoring
- **5 LangChain tools** — analyze_portfolio, get_stock_metrics, get_price_data, search_sec_filings, index_sec_filing

### 🚧 In Progress (Agents)
- Financial Planner agent (bull/base/bear scenarios)
- Client Comms agent (plain-English summaries)
- LangGraph multi-agent workflow with human-in-the-loop

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
│   ├── risk_assessor.py       # Portfolio risk + SEC filing analysis ✅
│   ├── financial_planner.py   # Scenario analysis (bull/base/bear)
│   └── client_comms.py        # Drafts personalized client summaries
│
├── data/                      # Data layer — fetching and storage
│   ├── market_data.py         # yfinance wrapper (prices, metrics) ✅
│   ├── sec_fetcher.py         # SEC EDGAR API + BeautifulSoup cleaning ✅
│   └── vector_store.py        # ChromaDB + HuggingFace embeddings ✅
│
├── tools/                     # LangChain tools for agents
│   └── portfolio_tools.py     # 5 tools agents can call ✅
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
│   ├── test_data_layer.py     # Data layer tests ✅ (8/8 passing)
│   └── test_tools.py          # Tools + agent tests ✅ (7/7 passing)
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
- Groq API key ([Get one free](https://console.groq.com))
- Gemini API key ([Get one free](https://aistudio.google.com/app/apikey)) — for embeddings only
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
# Edit .env and add your API keys
```

### Environment Variables

```env
# LLM (Groq — free and fast)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

# Embeddings (Gemini — free tier sufficient)
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# LangSmith (optional — for tracing)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=wealthadvisor

# App
APP_ENV=development
LOG_LEVEL=INFO
```

### Run Tests

```bash
# Data layer tests
python tests/test_data_layer.py

# Tools + agent tests
python tests/test_tools.py
```

Expected output:
```
✅ test_get_key_metrics          PASSED
✅ test_get_price_history        PASSED
✅ test_calculate_portfolio_metrics  PASSED
✅ test_get_cik                  PASSED
✅ test_get_recent_filings       PASSED
✅ test_fetch_filing_text        PASSED
✅ test_chunk_text               PASSED
✅ test_index_and_query          PASSED
✅ All tests passed!
```

---

## 🔍 How It Works — Under the Hood

### 1. SEC Filing Analysis (RAG Pipeline)

```
Apple 10-K (200 pages)
       ↓
BeautifulSoup strips HTML tags
       ↓
Skip to Item 1 (readable content starts here)
       ↓
Split into 1000-char chunks with 200-char overlap
       ↓
Each chunk → HuggingFace MiniLM Embedding (384 dimensions)
       ↓
Stored in ChromaDB (local, no API needed)
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
- **SEC insights** → material risks from filings with citations
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
| HuggingFace MiniLM | Local embeddings (runs on your machine) | Free |
| Groq API | LLM inference (LLaMA 3) | Free tier |

**Total running cost for development: $0**

---

## 🗺️ Roadmap

- [x] Data layer (market data, SEC fetcher, vector store)
- [x] HTML cleaning with BeautifulSoup
- [x] LangChain tools (5 tools)
- [x] Supervisor agent
- [x] Risk Assessor agent
- [ ] Financial Planner agent
- [ ] Client Comms agent
- [ ] LangGraph multi-agent workflow
- [ ] FastAPI backend
- [ ] Streamlit dashboard
- [ ] RAGAS evaluation harness
- [ ] Docker deployment
- [ ] PDF report export

---

## 👨‍💻 Author

**Chakravarthi Boora**
Applied AI Technical Analyst · Generative & Agentic AI · Wealth & Financial AI

[LinkedIn](https://linkedin.com) · [GitHub](https://github.com/chakri0176)

---

## ⚠️ Disclaimer

This project is for educational and informational purposes only. It does not constitute financial advice. Always consult a qualified financial advisor before making investment decisions.

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
