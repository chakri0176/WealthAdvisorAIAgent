# Data Layer Documentation

The data layer is the foundation of WealthAdvisor AI. It handles all data fetching, processing, and storage before any agent touches it.

---

## Overview

```
data/
├── market_data.py    → Live stock prices and metrics (yfinance)
├── sec_fetcher.py    → SEC EDGAR filing downloader + HTML cleaner
└── vector_store.py   → ChromaDB indexing and semantic search
```

Think of it as the **research department** — before any analyst (agent) can work, someone needs to pull the latest prices, download annual reports, and organize everything for fast searching.

---

## 1. market_data.py — Live Market Data ✅

### What it does
Fetches real-time and historical financial data for any US-listed stock using Yahoo Finance (yfinance).

### Functions

#### `get_key_metrics(ticker: str) -> dict`

Returns key financial metrics for a single stock.

```python
from data.market_data import get_key_metrics

result = get_key_metrics("AAPL")
# {
#   "ticker": "AAPL",
#   "company_name": "Apple Inc.",
#   "sector": "Technology",
#   "market_cap": 4346723172352,
#   "beta": 1.086,
#   "current_price": 295.95
# }
```

**What is Beta?**
| Beta | Meaning |
|------|---------|
| < 1.0 | Less volatile than market (defensive) |
| = 1.0 | Moves exactly with market |
| > 1.0 | More volatile than market (aggressive) |
| AAPL 1.086 | Slightly more volatile than S&P 500 |

#### `get_price_history(ticker: str, period: str = "1y") -> DataFrame`

Returns historical OHLCV data. Uses `.dropna()` to remove rows with missing closing prices (market holidays, after-hours data).

```python
df = get_price_history("AAPL", period="1y")
# Returns DataFrame with: Open, High, Low, Close, Volume
# Index: datetime, cleaned of timezone info
```

#### `calculate_portfolio_metrics(holdings: list) -> dict`

Analyzes an entire portfolio. Uses `try/except` so one bad ticker doesn't crash the full analysis.

```python
holdings = [
    {"ticker": "AAPL", "weight": 0.4, "shares": 100},
    {"ticker": "MSFT", "weight": 0.35, "shares": 50},
    {"ticker": "GOOGL", "weight": 0.25, "shares": 30},
]
result = calculate_portfolio_metrics(holdings)
# {"holdings": [...metrics per stock...], "num_positions": 3}
```

### Important Note on yfinance

yfinance is an **unofficial wrapper** around Yahoo Finance. It can occasionally:
- Return NaN for recent prices (use `.dropna()` to handle)
- Fail for delisted or non-US tickers
- Rate limit on too many concurrent requests

For production at scale, consider migrating to Alpha Vantage or Financial Modeling Prep APIs.

---

## 2. sec_fetcher.py — SEC Filing Data ✅

### What are SEC Filings?

Every US public company must file regular reports with the **SEC (Securities and Exchange Commission)**. These are publicly available on **EDGAR** (Electronic Data Gathering, Analysis, and Retrieval).

| Filing | Frequency | Contents | Value |
|--------|-----------|----------|-------|
| **10-K** | Annual (once/year) | Full financials, risk factors, business overview | Highest |
| **10-Q** | Quarterly (3x/year) | Shorter update, unaudited | Medium |
| **8-K** | Event-driven | Material events (acquisitions, CEO changes) | Situational |

The **Risk Factors section (Item 1A)** of a 10-K is gold — companies are legally required to disclose anything that could negatively impact their business. This is what our Risk Assessor agent reads.

### The HTML Problem and Solution

SEC filings are submitted as HTML/XBRL files. The raw text looks like:

```html
<span style="font-family:'Helvetica';font-size:9pt">
The Company's products may be affected by design defects...
</span>
```

We use **BeautifulSoup** to strip all tags:

```python
soup = BeautifulSoup(raw_text, "html.parser")
clean_text = soup.get_text(separator=" ", strip=True)
# Result: "The Company's products may be affected by design defects..."
```

Then skip the XBRL headers at the top of each file by jumping to "ITEM 1.":

```python
start = clean_text.find("ITEM 1.")
if start == -1:
    start = clean_text.find("Item 1.")
return clean_text[start:start + 50000]
```

### Functions

#### `get_cik(ticker: str) -> str`

Converts a stock ticker to SEC's internal company identifier (CIK number).

```python
get_cik("AAPL")  # → "0000320193"
get_cik("MSFT")  # → "0000789019"
```

Every public company has a unique 10-digit CIK. Required for all EDGAR API calls.

#### `get_recent_filings(ticker, form_type="10-K", count=3) -> list`

```python
filings = get_recent_filings("AAPL", form_type="10-K", count=3)
# [
#   {"ticker": "AAPL", "form": "10-K", 
#    "accessionNumber": "0000320193-25-000079", 
#    "filingDate": "2025-10-31"},
#   ...
# ]
```

#### `fetch_filing_text(accession_number, ticker, max_chars=50000) -> str`

Downloads, cleans, and returns readable filing text.

```python
text = fetch_filing_text("0000320193-25-000079", "AAPL")
# Returns clean text starting from "ITEM 1. Business..."
# Apple's actual 2025 annual report content
```

**Why 50,000 chars?**
Full 10-K filings are 500,000+ characters. The first 50K after "ITEM 1." covers the most valuable sections including all risk factors (Item 1A).

### Rate Limiting

SEC EDGAR asks developers to be polite. We add `time.sleep(0.1)` between requests. For high-volume indexing, stay under 10 requests/second.

---

## 3. vector_store.py — Semantic Search ✅

### The Problem

A 10-K filing is 200+ pages. Sending all of it to an AI agent every time would be:
- **Slow** — 100K+ tokens takes 30+ seconds to process
- **Expensive** — costs money per token
- **Unnecessary** — agent only needs the relevant parts

### The Solution: Semantic Search

We convert text into **embeddings** (vectors of numbers) that capture meaning. Similar meaning → similar numbers → ChromaDB finds related content instantly.

```
"Apple faces supply chain risks"
→ [0.23, -0.45, 0.12, ...] (384 numbers)

"iPhone manufacturing dependencies"  
→ [0.21, -0.43, 0.14, ...] (very similar!)

"Best pizza recipes"
→ [0.89, 0.34, -0.67, ...] (very different)
```

When an agent searches "What are Apple's risk factors?", ChromaDB finds chunks whose numbers are most similar — even if they use different words.

### Why HuggingFace MiniLM (not Gemini/OpenAI)?

During development, Gemini embedding API hit rate limits when indexing 3 companies simultaneously (63 chunks × 3 = 189 API calls). Switch to local embeddings:

| Feature | Gemini Embeddings | HuggingFace MiniLM |
|---------|-----------------|-------------------|
| Cost | API calls | Free (local) |
| Rate limits | 1500/day free | Unlimited |
| Setup | API key | pip install |
| Speed | ~2s per batch | ~5-8s per filing |
| Dimensions | 768 | 384 |
| Quality | Higher | Good enough |

For a wealth advisor tool analyzing 3-10 stocks, MiniLM is more than sufficient.

### Functions

#### `chunk_text(text, chunk_size=1000, overlap=200) -> list`

Splits long text into overlapping chunks.

```python
chunks = chunk_text(apple_10k_text)
# Returns ~63 chunks of 1000 chars each
# Each chunk overlaps 200 chars with neighbors
```

**Why overlap?** Without overlap, a sentence split across two chunks loses context. With 200-char overlap, each chunk shares content with neighbors — no information lost at boundaries.

#### `get_embeddings() -> HuggingFaceEmbeddings`

Returns the local MiniLM embedding model. Downloads ~90MB on first run, cached forever.

#### `get_collection() -> ChromaDB collection`

Connects to (or creates) the local ChromaDB database at `./chroma_db/`.

#### `index_document(text, doc_id, metadata) -> int`

Full indexing pipeline:
```python
chunks = chunk_text(text)                          # split
embeddings = embedder.embed_documents(chunks)       # embed locally
collection.upsert(documents, embeddings, metadata)  # store
return len(chunks)  # 63
```

#### `query(query_text, n_results=5) -> list`

Semantic search:
```python
results = query("What are Apple's main risk factors?")
# Returns top 5 most relevant chunks:
# [
#   {
#     "text": "The Company's products may be affected by design defects...",
#     "metadata": {"ticker": "AAPL", "form_type": "10-K", "filing_date": "2025-10-31"},
#     "distance": 0.234  # lower = more relevant
#   },
#   ...
# ]
```

### Important: Delete chroma_db When Changing Models

If you switch embedding models (e.g., MiniLM 384-dim → Gemini 768-dim), the dimensions won't match and queries will fail:

```
ChromaDB error: Collection expecting 384 dimensions, got 768
```

Fix: delete the `chroma_db/` folder and re-index everything.

```bash
rmdir /s /q chroma_db  # Windows
rm -rf chroma_db       # Mac/Linux
```

---

## Test Results

```bash
python tests/test_data_layer.py
```

```
✅ test_get_key_metrics           AAPL: $295.95, Beta: 1.086
✅ test_get_price_history         63 trading days, no NaN values
✅ test_calculate_portfolio_metrics  3 positions processed correctly
✅ test_get_cik                   AAPL: 0000320193
✅ test_get_recent_filings        3 real 10-K filings found
✅ test_fetch_filing_text         50,000 chars, clean text
✅ test_chunk_text                63 chunks, 1000 chars each
✅ test_index_and_query           63 indexed, 5 results returned
✅ All 8 tests passed!
```

---

## Known Limitations

| Limitation | Impact | Future Fix |
|-----------|--------|------------|
| yfinance is unofficial | Can break randomly | Migrate to Alpha Vantage |
| 50K char limit on filings | Misses later sections | Increase limit or multi-pass |
| US stocks only | No Indian/UK stocks | Add .NS/.L suffix support |
| ChromaDB is local | Can't share across servers | Migrate to Qdrant/Pinecone |
| No filing update detection | Stale data if not re-indexed | Add filing date change detection |
