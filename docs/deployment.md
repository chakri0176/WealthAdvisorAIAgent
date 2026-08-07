# Deployment Guide

This guide covers deploying WealthAdvisor AI from local development to production.

---

## Architecture Overview

```
Internet
    │
    ├── https://wealthadvisor.streamlit.app  (Streamlit Cloud - FREE)
    │        │
    │        │ HTTP POST /analyze
    │        │ HTTP POST /review
    │        ▼
    └── https://wealthadvisor-api.onrender.com  (Render - FREE)
             │
             ├── LangGraph agents
             ├── ChromaDB (ephemeral)
             └── SQLite (ephemeral on free tier)
```

---

## Option 1 — Streamlit Cloud + Render (Recommended, Free)

### Step 1 — Deploy FastAPI to Render

1. Go to **https://render.com** and sign up with GitHub

2. Click **"New +"** → **"Web Service"**

3. Connect your GitHub repository

4. Configure the service:
   ```
   Name:          wealthadvisor-api
   Runtime:       Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```

5. Add environment variables (click "Environment"):
   ```
   GROQ_API_KEY=your_key
   GROQ_MODEL=llama-3.3-70b-versatile
   GOOGLE_API_KEY=your_key
   GEMINI_API_KEY=your_key
   GEMINI_MODEL=gemini-2.5-flash
   APP_ENV=production
   ```

6. Click **"Create Web Service"**

7. Wait 3-5 minutes for first deploy

8. Copy your API URL: `https://wealthadvisor-api-xxxx.onrender.com`

### Step 2 — Deploy Dashboard to Streamlit Cloud

1. Go to **https://share.streamlit.io** and sign in with GitHub

2. Click **"New app"**

3. Configure:
   ```
   Repository:  your-github-username/wealthadvisor-ai
   Branch:      main
   Main file:   ui/dashboard.py
   ```

4. Click **"Advanced settings"** → Add secrets:
   ```toml
   GROQ_API_KEY = "your_key"
   GROQ_MODEL = "llama-3.3-70b-versatile"
   GOOGLE_API_KEY = "your_key"
   GEMINI_API_KEY = "your_key"
   API_BASE = "https://wealthadvisor-api-xxxx.onrender.com"
   ```

5. Click **"Deploy"**

6. Your app is live at: `https://your-username-wealthadvisor.streamlit.app`

### Free Tier Limitations

| Platform | Limitation | Impact |
|----------|-----------|--------|
| Render | Sleeps after 15min inactivity | First request after sleep takes ~30s |
| Render | 512MB RAM | ChromaDB may need cleanup |
| Streamlit Cloud | 1GB RAM | Should be fine |
| Both | Shared CPU | Slower than paid tier |

---

## Option 2 — Railway (Easiest, $5/month)

Railway handles both services in one place.

1. Go to **https://railway.app** and sign up

2. Click **"New Project"** → **"Deploy from GitHub repo"**

3. Select your repository

4. Add two services:

**Service 1 — API:**
```
Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

**Service 2 — Dashboard:**
```
Start Command: streamlit run ui/dashboard.py --server.port $PORT --server.address 0.0.0.0
```

5. Add environment variables in Railway dashboard

6. Both services get public URLs automatically

**Advantage over Render:** Never sleeps, faster cold starts, easier multi-service management.

---

## Option 3 — DigitalOcean VPS ($6/month)

For full control and persistent storage.

### Setup

```bash
# 1. Create a $6/month Droplet (Ubuntu 24.04)

# 2. SSH into your server
ssh root@your-server-ip

# 3. Install Docker
curl -fsSL https://get.docker.com | sh

# 4. Clone your repo
git clone https://github.com/YOUR_USERNAME/wealthadvisor-ai.git
cd wealthadvisor-ai

# 5. Set up environment
cp .env.example .env
nano .env  # add your API keys

# 6. Run with Docker Compose
docker-compose up -d

# 7. Set up Nginx reverse proxy (optional)
apt install nginx
# Configure nginx to proxy 8000 → api and 8501 → dashboard
```

**Advantage:** Persistent ChromaDB and SQLite, full control, no sleep issues.

---

## Environment Variables Reference

```env
# Required
GROQ_API_KEY=           # Get free at console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# Required for embeddings
GOOGLE_API_KEY=         # Get free at aistudio.google.com
GEMINI_API_KEY=         # Same key as GOOGLE_API_KEY
GEMINI_MODEL=gemini-2.5-flash

# Dashboard → API connection
API_BASE=http://localhost:8000           # local development
API_BASE=https://your-api.onrender.com  # production

# Optional
APP_ENV=production
LOG_LEVEL=INFO
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=      # LangSmith tracing (optional)
LANGCHAIN_PROJECT=wealthadvisor
```

---

## Pre-Deployment Checklist

```
□ All tests passing locally
  python tests/test_data_layer.py
  python tests/test_tools.py
  python tests/test_agents.py
  python tests/test_graph.py
  python tests/test_client_memory.py

□ API_BASE updated in dashboard.py
  API_BASE = os.getenv("API_BASE", "http://localhost:8000")

□ .env.example is up to date

□ .gitignore includes:
  .env
  chroma_db/
  clients/wealthadvisor.db
  __pycache__/
  venv/

□ requirements.txt is complete and up to date

□ Latest code pushed to GitHub
  git add .
  git commit -m "feat: ready for deployment"
  git push
```

---

## Post-Deployment Testing

After deployment, test each endpoint:

```bash
# 1. Health check
curl https://your-api.onrender.com/health
# Expected: {"status": "ok"}

# 2. Open API docs
# https://your-api.onrender.com/docs

# 3. Open dashboard
# https://your-username-wealthadvisor.streamlit.app

# 4. Run a test analysis
# - Add AAPL 50%, MSFT 50% in sidebar
# - Click Run Analysis
# - Wait 60 seconds
# - Approve the analysis
# - Check client summary appears
```

---

## Production Considerations

### ChromaDB Persistence

On free tier (Render/Railway), the filesystem is **ephemeral** — ChromaDB data resets on redeploy. This means SEC filings need to be re-indexed after each deploy.

**Solution for production:**
- Use Qdrant Cloud (free tier available) instead of ChromaDB
- Or use Pinecone (free tier: 1 index)

### SQLite Persistence

Same issue — SQLite resets on redeploy.

**Solution for production:**
- Migrate to PostgreSQL (Render offers free PostgreSQL)
- Use Supabase free tier (PostgreSQL)

### Scaling

Current architecture handles ~10 concurrent users. For more:
- Add Redis for caching (Upstash free tier)
- Add background task queue (Celery + Redis)
- Separate ChromaDB to dedicated service

---

## Cost Projection

### Development (Now)
```
Groq API:           Free (100 RPM)
Gemini API:         Free (1500/day)
HuggingFace:        Free (local)
SEC EDGAR:          Free
yfinance:           Free
Render:             Free
Streamlit Cloud:    Free
Total:              $0/month
```

### Early Production (10-50 users)
```
Render (paid):      $7/month
Railway:            $5/month
Domain name:        $1/month
Groq API:           Free or $20/month
Total:              ~$13-28/month
```

### Growth (100+ users)
```
DigitalOcean:       $24/month (4GB RAM)
PostgreSQL:         $7/month (Render)
Qdrant Cloud:       $25/month
Domain + SSL:       $2/month
Total:              ~$58/month
```

At $49/month per user, you need just **2 paying users** to cover infrastructure costs.

---

## Monitoring

### Health Monitoring (Free)
Use **UptimeRobot** (free) to ping your `/health` endpoint every 5 minutes:
- Prevents Render from sleeping
- Alerts you if the API goes down
- Free for up to 50 monitors

### Error Tracking (Free)
Add Sentry for error tracking:
```python
# In api/main.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

### Usage Analytics (Free)
Add simple logging to track:
- How many analyses per day
- Which clients are most active
- Most common error types
