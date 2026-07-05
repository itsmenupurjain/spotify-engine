# 🎵 Spotify Discovery Engine
## AI-Powered Review Discovery Intelligence Platform
### Spotify Growth Team

> **Answers the question:** *"Why do Spotify users with intent to discover new music still end up listening to the same familiar content repeatedly — and what unmet needs are driving this behavior?"*

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PM Dashboard (Next.js 14)                   │
│   Intelligence Home │ NL Query │ Themes │ Segments │ Opps │ Quotes│
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────────┐
│                     FastAPI Backend                              │
│   /query (RAG) │ /themes │ /segments │ /opportunities │ /health  │
└──────────┬──────────────────────────────┬───────────────────────┘
           │ AI Layer                     │ Scheduler (APScheduler)
     ┌─────▼─────┐                  ┌────▼───────────────────────┐
     │  Claude   │                  │ ingest (weekly)             │
     │ Sonnet    │                  │ classify (daily)            │
     │ GPT-4o    │                  │ embed (daily)               │
     │ Embedder  │                  │ cluster (weekly)            │
     └─────┬─────┘                  │ synthesize (daily)          │
           │                        │ health_check (15 min)       │
┌──────────▼──────────────────────────────────────────────────────┐
│              PostgreSQL 16 + pgvector                            │
│  raw_reviews │ classified_reviews │ themes │ synthesis_cache      │
└──────────────────────────▲──────────────────────────────────────┘
                           │ Ingestion Pipeline
         ┌─────────────────┼──────────────────────┐
    App Store        Play Store               Reddit
    Play Store    Community Forum           Twitter/X
```

---

## 🚀 Quick Start (Development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker Desktop

### One-command setup

```bash
# Clone and setup everything
git clone <repo-url>
cd spotify

# Full setup with seed data
python scripts/setup.py --all
```

### Manual setup

```bash
# 1. Environment
cp .env.example .env
# Edit .env with your API keys

# 2. Start database
docker compose up -d db

# 3. Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
python ../scripts/seed_data.py    # Load demo data (no API keys needed)
uvicorn app.main:app --reload --port 8000

# 4. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** 🎉

---

## 🔑 API Keys Required

| Key | Purpose | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude — AI classification + synthesis | ✅ Core |
| `OPENAI_API_KEY` | text-embedding-3-small + GPT-4o fallback | ✅ Core |
| `REDDIT_CLIENT_ID` | Reddit scraper (PRAW) | Optional |
| `REDDIT_CLIENT_SECRET` | Reddit scraper | Optional |
| `TWITTER_BEARER_TOKEN` | Twitter API v2 | Optional |
| `APIFY_API_TOKEN` | Twitter fallback scraper | Optional |

> **Note:** Without API keys, use `python scripts/seed_data.py` to load 600+ realistic synthetic reviews for full dashboard demo.

---

## 📊 Dashboard Views

| View | URL | Description |
|---|---|---|
| Intelligence Home | `/` | Overview: themes, unmet needs, sentiment, segments |
| Ask a Question | `/query` | Natural language query with AI-synthesized answers |
| Theme Explorer | `/themes` | Deep-dive into each identified theme |
| Segment Breakdown | `/segments` | Per-segment complaints, JTBD, and quotes |
| Opportunity Map | `/opportunities` | Bubble chart: frequency × severity × cross-source |
| Quote Library | `/quotes` | Filter, copy, and save verbatim user quotes |

---

## 🤖 AI Pipeline

### Classification (Claude Sonnet 4.6)
- 10 complaint categories (algorithm staleness, genre bubble, trust erosion, etc.)
- 7 user segments (active explorer stuck, mood regulator, etc.)
- Extracts: JTBD statements, unmet needs, frustration phrases
- Batch size: 50 reviews/call · Confidence threshold: 0.7

### Embeddings (OpenAI text-embedding-3-small)
- 1536-dimensional vectors stored in pgvector
- Used for: semantic search, RAG queries, theme clustering

### Theme Clustering
- k-means on frustration phrase embeddings
- Silhouette score optimization for k
- AI-generated theme names and descriptions

### RAG Query Engine
- Embed query → cosine similarity search → intent extraction → SQL filters → AI synthesis
- Returns: structured answer, evidence, confidence level, follow-up questions

---

## ⏰ Scheduled Jobs

| Job | Schedule | Action |
|---|---|---|
| `ingest_all_sources` | Sunday 2am UTC | Scrape all 5 sources |
| `classify_new_reviews` | Daily 1am UTC | AI classify up to 500 reviews |
| `embed_new_reviews` | Daily 2am UTC | Generate embeddings for up to 200 reviews |
| `refresh_synthesis_cache` | Daily 3am UTC | Recompute all dashboard aggregations |
| `update_clusters` | Monday 4am UTC | Re-cluster themes with new data |
| `health_check` | Every 15 min | Monitor pipeline health, send alerts |

Manual trigger: `POST /api/pipeline/trigger/{job_id}`

---

## 🚢 Deployment

### Railway (Backend)
```bash
railway login
railway up
# Set env vars in Railway dashboard
```

### Vercel (Frontend)
```bash
cd frontend
vercel --prod
# Set NEXT_PUBLIC_API_URL to your Railway URL
```

### Docker (Full Stack)
```bash
docker compose up --build
```

---

## 📁 Project Structure

```
spotify/
├── backend/
│   ├── app/
│   │   ├── ai/           # Classifier, embedder, clusterer, synthesizer, RAG
│   │   ├── api/          # FastAPI route handlers
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── pipeline/     # Cleaner + orchestrator
│   │   ├── scrapers/     # 5 source scrapers
│   │   ├── services/     # Monitoring service
│   │   ├── config.py     # Settings
│   │   ├── database.py   # SQLAlchemy + pgvector
│   │   ├── main.py       # FastAPI app
│   │   └── scheduler.py  # APScheduler jobs
│   ├── alembic/          # Database migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/          # Next.js App Router pages (6 views)
│       ├── components/   # Sidebar
│       └── lib/          # Typed API client
├── scripts/
│   ├── seed_data.py      # Synthetic data generator
│   ├── setup.py          # One-command setup
│   └── init_db.sql       # DB init SQL
├── docker-compose.yml    # Local + production orchestration
├── railway.json          # Railway deployment config
└── .env.example          # Environment variable template
```

---

## 🧪 Acceptance Criteria (from spec)

- [ ] 500+ reviews ingested across all 5 sources
- [ ] 8-12 distinct discovery themes identified
- [ ] NL query response time < 3 seconds
- [ ] Classification accuracy > 80% (sampled)
- [ ] Dashboard loads in < 2 seconds
- [ ] Embeddings for 95%+ of classified relevant reviews
