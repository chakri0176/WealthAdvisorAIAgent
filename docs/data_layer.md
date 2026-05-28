# Data Layer Documentation

The data layer is the foundation of WealthAdvisor AI. It handles all data fetching, processing, and storage before any agent touches it.

---

## What is the Data Layer?

Think of it as the **research department** of the firm. Before any analyst (agent) can do their job, someone needs to:
- Pull the latest stock prices
- Download the company's annual reports
- Organize that information so it can be searched quickly

That's exactly what our 3 data files do.

---

## 1. market_data.py — Live Market Data

### What it does
Fetches real-time and historical financial data for any publicly traded stock using Yahoo Finance.

### Functions

#### `get_key_metrics(ticker: str) -> dict`
Returns key financial metrics for a single stock.

**Example:**
```python
from data.market_data import get_key_metrics
result = get_key_metrics("AAPL")
# Returns:
# {
#   "ticker": "AAPL",
#   "company_name": "Apple Inc.",
#   "sector": "Technology",
#   "market_cap": 4565564915712,
#   "beta": 1.065,
#   "current_price": 310.85
# }
```

**What is Beta?**
Beta measures how much a stock moves relative to the market:
- Beta = 1.0 → moves exactly with the market
- Beta > 1.0 → more volatile than market (higher risk)
- Beta < 1.0 → less volatile than market (lower risk)
- Apple's beta of 1.065 → slightly more volatile than market

#### `get_price_history(ticker: str, period: str = "1y") -> DataFrame`
Returns historical price data as a pandas DataFrame.

**Example:**
```python
from data.market_data import get_price_history
df = get_price_history("AAPL", period="1y")
# Returns DataFrame with columns: Open, High, Low, Close, Volume
```

**Period options:** `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`

#### `calculate_portfolio_metrics(holdings: list) -> dict`
Analyzes an entire portfolio at once.

**Example:**
```python
holdings = [
    {"ticker": "AAPL", "weight": 0.4, "shares": 100},
    {"ticker": "MSFT", "weight": 0.35, "shares": 50},
    {"ticker": "GOOGL", "weight": 0.25, "shares": 30},
]
result = calculate_portfolio_metrics(holdings)
# Returns:
# {
#   "holdings": [...metrics per stock...],
#   "num_positions": 3
# }
```

---

## 2. sec_fetcher.py — SEC Filing Data

### What is SEC EDGAR?
Every public company in the US must file regular financial reports with the SEC (Securities and Exchange Commission). These reports are publicly available on EDGAR (Electronic Data Gathering, Analysis, and Retrieval system).

### What are 10-K and 10-Q filings?

| Filing | Frequency | Contents |
|--------|-----------|----------|
| **10-K** | Annual | Full year financials, risk factors, business overview |
| **10-Q** | Quarterly | Shorter quarterly update, unaudited |

The **Risk Factors** section of a 10-K is particularly valuable — companies are legally required to disclose anything that could negatively impact their business.

### Functions

#### `get_cik(ticker: str) -> str`
Converts a stock ticker to SEC's internal company identifier (CIK).

```python
from data.sec_fetcher import get_cik
cik = get_cik("AAPL")
# Returns: "0000320193"
```

Every company has a unique 10-digit CIK. Apple's is 0000320193. We need this to query EDGAR's API.

#### `get_recent_filings(ticker: str, form_type: str = "10-K", count: int = 3) -> list`
Fetches a list of recent filings for a company.

```python
from data.sec_fetcher import get_recent_filings
filings = get_recent_filings("AAPL", form_type="10-K", count=3)
# Returns:
# [
#   {"ticker": "AAPL", "form": "10-K", "accessionNumber": "0000320193-25-000079", "filingDate": "2025-10-31"},
#   {"ticker": "AAPL", "form": "10-K", "accessionNumber": "0000320193-24-000123", "filingDate": "2024-11-01"},
#   {"ticker": "AAPL", "form": "10-K", "accessionNumber": "0000320193-23-000106", "filingDate": "2023-11-03"}
# ]
```

#### `fetch_filing_text(accession_number: str, ticker: str, max_chars: int = 50000) -> str`
Downloads the actual text content of a filing.

```python
from data.sec_fetcher import fetch_filing_text
text = fetch_filing_text("0000320193-25-000079", "AAPL")
# Returns first 50,000 characters of Apple's 2025 10-K
```

**Why 50,000 chars?**
Full 10-K filings can be 500,000+ characters. We take the first 50K which covers the most important sections (business overview, risk factors). The RAG pipeline then finds the specific relevant parts.

### Rate Limiting
SEC EDGAR requires a `User-Agent` header and asks developers to limit requests. We add `time.sleep(0.1)` between requests to be a good citizen.

---

## 3. vector_store.py — Semantic Search

### The Problem
A 10-K filing is 200+ pages. We can't send all of it to an AI agent every time — it would be slow and expensive. We need a way to find only the relevant parts.

### The Solution: Vector Search
We convert text into numbers (embeddings) that capture meaning. Similar meaning → similar numbers → easy to find related content.

```
"Apple faces supply chain risks"  → [0.23, -0.45, 0.12, ...]
"iPhone manufacturing dependencies" → [0.21, -0.43, 0.14, ...]
                                      ↑ Very similar numbers!
```

### Functions

#### `chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list`
Splits a long document into overlapping chunks.

```python
from data.vector_store import chunk_text
chunks = chunk_text(apple_10k_text)
# Returns list of ~63 chunks, each 1000 chars
# Chunks overlap by 200 chars to avoid cutting sentences
```

**Why overlap?**
Without overlap, a sentence split across two chunks loses context. With 200-char overlap, each chunk shares content with its neighbors.

#### `get_embeddings()`
Returns a Gemini embedding model that converts text to vectors.

#### `get_collection()`
Connects to (or creates) the ChromaDB database on disk.

#### `index_document(text: str, doc_id: str, metadata: dict) -> int`
Full pipeline: chunk → embed → store.

```python
from data.vector_store import index_document
chunks_stored = index_document(
    text=apple_filing_text,
    doc_id="AAPL_10K_2025",
    metadata={"ticker": "AAPL", "form_type": "10-K", "filing_date": "2025-10-31"}
)
# Returns: 63 (number of chunks stored)
```

After calling this, a `chroma_db/` folder appears in your project containing the indexed data.

#### `query(query_text: str, n_results: int = 5) -> list`
Semantic search — finds the most relevant chunks for a question.

```python
from data.vector_store import query
results = query("What are Apple's main risk factors?", n_results=5)
# Returns top 5 most semantically relevant chunks
# Each result: {"text": "...", "metadata": {...}, "distance": 0.234}
```

**What is distance?**
Lower distance = more similar to your query. Results are sorted by distance (most relevant first).

---

## Running the Tests

```bash
python tests/test_data_layer.py
```

All 8 tests should pass:
```
✅ test_get_key_metrics
✅ test_get_price_history
✅ test_calculate_portfolio_metrics
✅ test_get_cik
✅ test_get_recent_filings
✅ test_fetch_filing_text
✅ test_chunk_text
✅ test_index_and_query
```

---

## Important Notes

- **chroma_db/** is gitignored — it's generated locally and can be large
- **SEC rate limits** — don't make more than 10 requests/second to EDGAR
- **yfinance** is unofficial — Yahoo Finance can occasionally return empty data for some tickers
- **Embeddings cost** — each call to Gemini embedding API uses tokens; batch your indexing
