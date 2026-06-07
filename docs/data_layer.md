# Data Layer Documentation

The data layer is the foundation of WealthAdvisor AI. It handles all data fetching, processing, and storage before any agent touches it.

---

## What is the Data Layer?

Think of it as the **research department** of the firm. Before any analyst (agent) can do their job, someone needs to:
- Pull the latest stock prices
- Download the company's annual reports
- Clean and organize that information so it can be searched quickly

That's exactly what our 3 data files do.

---

## 1. market_data.py — Live Market Data ✅

### What it does
Fetches real-time and historical financial data for any publicly traded stock using Yahoo Finance.

### Functions

#### `get_key_metrics(ticker: str) -> dict`
Returns key financial metrics for a single stock.

```python
from data.market_data import get_key_metrics
result = get_key_metrics("AAPL")
# Returns:
# {
#   "ticker": "AAPL",
#   "company_name": "Apple Inc.",
#   "sector": "Technology",
#   "market_cap": 4514011676672,
#   "beta": 1.086,
#   "current_price": 307.34
# }
```

**What is Beta?**
- Beta = 1.0 → moves exactly with the market
- Beta > 1.0 → more volatile (higher risk)
- Beta < 1.0 → less volatile (lower risk)

#### `get_price_history(ticker: str, period: str = "1y") -> DataFrame`
Returns historical OHLCV price data as a pandas DataFrame.

#### `calculate_portfolio_metrics(holdings: list) -> dict`
Analyzes an entire portfolio. Uses try/except so one bad ticker doesn't crash the whole analysis.

---

## 2. sec_fetcher.py — SEC Filing Data ✅

### What are SEC Filings?
Every public US company must file regular reports with the SEC. These are publicly available on EDGAR.

| Filing | Frequency | Key Contents |
|--------|-----------|-------------|
| **10-K** | Annual | Risk factors, full financials, business overview |
| **10-Q** | Quarterly | Shorter update, unaudited |

The **Risk Factors** section (Item 1A) is gold — companies legally must disclose anything that could hurt their business.

### The HTML Cleaning Problem (and fix)

SEC filings are submitted as HTML/XBRL files. The raw text looks like:
```html
<span style="font-family:'Helvetica'">The Company's products may be
affected by design defects...</span>
```

We use **BeautifulSoup** to strip all HTML tags, leaving clean text:
```
The Company's products may be affected by design defects...
```

Then we skip to **Item 1** to bypass XBRL headers at the top of each file.

### Functions

#### `get_cik(ticker: str) -> str`
Converts ticker to SEC CIK number.
```python
get_cik("AAPL")  # → "0000320193"
```

#### `get_recent_filings(ticker, form_type="10-K", count=3) -> list`
Fetches list of recent filings with dates and accession numbers.

#### `fetch_filing_text(accession_number, ticker, max_chars=50000) -> str`
Downloads filing, strips HTML with BeautifulSoup, skips to Item 1, returns clean text.

```python
# Pipeline inside fetch_filing_text:
raw_html = requests.get(sec_url).text
soup = BeautifulSoup(raw_html, "html.parser")
clean_text = soup.get_text(separator=" ", strip=True)
start = clean_text.find("ITEM 1.")  # skip headers
return clean_text[start:start + 50000]
```

---

## 3. vector_store.py — Semantic Search ✅

### The Problem
A 10-K filing is 200+ pages. Sending all of it to an AI agent every time would be slow and expensive.

### The Solution: Local Vector Search

We use **HuggingFace all-MiniLM-L6-v2** — a small, fast embedding model that runs 100% on your machine. No API calls, no quota limits.

```
"Apple faces supply chain risks"  → [0.23, -0.45, 0.12, ...]  (384 numbers)
"iPhone manufacturing dependency" → [0.21, -0.43, 0.14, ...]  (very similar!)
```

Similar meaning → similar numbers → ChromaDB finds related content instantly.

### Why we switched from Gemini to HuggingFace embeddings

During development, Gemini embedding API hit rate limits when indexing multiple SEC filings (63 chunks × multiple companies = hundreds of API calls). HuggingFace MiniLM:
- Runs locally — no API calls
- No quota limits
- Downloads once (~90MB), cached forever
- Fast enough for development (5-8 seconds per filing)

### Functions

#### `chunk_text(text, chunk_size=1000, overlap=200) -> list`
Splits long text into overlapping chunks. Overlap prevents cutting sentences mid-thought.

#### `get_embeddings() -> HuggingFaceEmbeddings`
Returns the local MiniLM embedding model.

#### `get_collection() -> ChromaDB collection`
Connects to (or creates) the local ChromaDB database.

#### `index_document(text, doc_id, metadata) -> int`
Full pipeline: chunk → embed locally → store in ChromaDB.

```python
# What happens inside:
chunks = chunk_text(text)              # split into 63 pieces
embedder = get_embeddings()            # load MiniLM locally
embeddings = embedder.embed_documents(chunks)  # 384-dim vectors
collection.upsert(documents=chunks, embeddings=embeddings, ...)
```

#### `query(query_text, n_results=5) -> list`
Semantic search — finds most relevant chunks for a question.

```python
results = query("What are Apple's main risk factors?")
# Returns:
# [
#   {
#     "text": "The Company's products may be affected by design defects...",
#     "metadata": {"ticker": "AAPL", "form_type": "10-K", ...},
#     "distance": 0.234  # lower = more relevant
#   },
#   ...
# ]
```

---

## Running the Tests

```bash
# Data layer
python tests/test_data_layer.py

# Tools + agents
python tests/test_tools.py
```

### Current Test Results

```
test_data_layer.py:
✅ test_get_key_metrics
✅ test_get_price_history
✅ test_calculate_portfolio_metrics
✅ test_get_cik
✅ test_get_recent_filings
✅ test_fetch_filing_text
✅ test_chunk_text
✅ test_index_and_query
✅ All 8 tests passed!

test_tools.py:
✅ test_get_stock_metrics
✅ test_get_price_data
✅ test_analyze_portfolio
✅ test_index_sec_filing
✅ test_search_sec_filings
✅ test_supervisor
✅ test_risk_assessor
✅ All 7 tests passed!
```

---

## Important Notes

- **chroma_db/** is gitignored — generated locally, can be large
- **Delete chroma_db/** whenever you change embedding models (dimension mismatch)
- **SEC rate limits** — we add `time.sleep(0.1)` between requests
- **yfinance** is unofficial — can occasionally return empty data
- **MiniLM model** downloads to `~/.cache/huggingface/` on first run
