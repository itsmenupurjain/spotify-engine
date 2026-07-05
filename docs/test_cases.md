# Test Cases & Edge Cases — Spotify Discovery Engine

This document outlines the testing strategy, expected behaviors, and critical edge cases for each of the 7 implementation phases of the Spotify Discovery Engine.

---

## Phase 1: Project Scaffolding & Infrastructure

### 🧪 Test Cases (Expected Behavior)
1. **Database Initialization**: `docker compose up db` successfully starts PostgreSQL 16.
2. **pgvector Extension**: The `vector` and `pgcrypto` extensions are successfully enabled upon database creation.
3. **ORM Models**: SQLAlchemy correctly maps all 9 models to the database schema.
4. **Migrations**: `alembic upgrade head` successfully creates all tables, relationships, and vector columns without errors.
5. **FastAPI Startup**: `uvicorn app.main:app` starts successfully and exposes the `/docs` Swagger UI.

### ⚠️ Edge Cases & Boundary Conditions
1. **Missing Extensions**: The target PostgreSQL instance lacks the `pgvector` extension (e.g., managed DBs like AWS RDS where it must be explicitly added).
2. **Environment Variables**: The `.env` file is missing or contains malformed database URLs.
3. **Port Conflicts**: Port `5432` or `8000` is already in use by another local service.
4. **Connection Drops**: The database becomes unavailable momentarily during application startup.

---

## Phase 2: Data Ingestion Layer

### 🧪 Test Cases (Expected Behavior)
1. **Scraper Execution**: All 5 scrapers (App Store, Play Store, Reddit, Community, Twitter) successfully fetch recent data.
2. **Deduplication**: The `DataCleaner` successfully identifies and drops duplicate reviews using SHA-256 hashes.
3. **Language Filtering**: Non-English reviews are accurately detected and discarded.
4. **Relevance Filtering**: Reviews not containing music discovery keywords are filtered out.
5. **Orchestrator**: The `PipelineOrchestrator` successfully chains scraping, cleaning, and database insertion in a single run.

### ⚠️ Edge Cases & Boundary Conditions
1. **API Rate Limiting (HTTP 429)**: Reddit or Twitter APIs return rate limit errors. The backoff/retry logic must handle this gracefully.
2. **DOM Changes**: The Spotify Community forum changes its HTML structure, breaking the Playwright scraper.
3. **Malformed Data**: APIs return missing fields (e.g., null review bodies or missing dates).
4. **Encoding Issues**: Reviews containing complex emojis, Zalgo text, or mixed encodings break database insertion.
5. **Pagination Traps**: Infinite loops caused by scrapers not correctly detecting the end of a paginated list.

---

## Phase 3: AI Processing Layer

### 🧪 Test Cases (Expected Behavior)
1. **Classification**: Claude Sonnet successfully categorizes a review into one of the 10 predefined complaint categories and 7 user segments.
2. **Embedding**: OpenAI successfully generates 1536-dimensional vectors for the reviews.
3. **Clustering**: K-Means clustering groups semantically similar reviews into themes, and AI assigns human-readable labels.
4. **RAG Retrieval**: The `pgvector` cosine similarity search returns the most relevant reviews for a given natural language query.
5. **Synthesis**: The daily aggregator correctly computes metrics like sentiment distribution and cross-source frequency.

### ⚠️ Edge Cases & Boundary Conditions
1. **Context Window Exceeded**: Exceptionally long Reddit posts exceed the token limit of the Claude or OpenAI APIs.
2. **AI Refusals / Hallucinations**: Claude refuses to classify a review containing profanity, or hallucinates categories not in the enum.
3. **Too Few Samples for Clustering**: K-Means clustering fails or produces a silhouette score error because there are fewer than `k` data points available.
4. **Embedding API Outage**: The OpenAI API is down, halting the pipeline. The system must queue these reviews for later embedding (`embedding_pending = True`).
5. **Vague RAG Queries**: The user asks an overly broad query ("tell me everything"), resulting in low-relevance vector matches.

---

## Phase 4: API Layer

### 🧪 Test Cases (Expected Behavior)
1. **Health Check**: `GET /api/health` returns a 200 OK with database and API key statuses.
2. **Pagination**: `GET /api/reviews?limit=10&offset=20` returns the correct slice of data.
3. **RAG Endpoint**: `POST /api/query` successfully triggers the AI engine and returns a synthesized answer with citations.
4. **CORS Headers**: API accepts requests from the allowed frontend origins (e.g., `localhost:3000`).

### ⚠️ Edge Cases & Boundary Conditions
1. **Deep Pagination**: A user requests `offset=1000000`, which could cause a slow sequential scan in PostgreSQL.
2. **Slow AI Responses**: The `/api/query` endpoint takes longer than standard HTTP timeout windows (e.g., >30s) due to Claude API latency.
3. **Rate Limit Breaches**: A user spams the `/api/query` endpoint, triggering the `slowapi` rate limiter (HTTP 429).
4. **Invalid Inputs**: Missing required JSON body parameters in POST requests, which must be caught by Pydantic validation.

---

## Phase 5: Dashboard Frontend

### 🧪 Test Cases (Expected Behavior)
1. **Navigation**: Clicking sidebar links instantly routes to the correct view without full page reloads.
2. **Data Rendering**: Charts (Recharts) render correctly using data fetched from the API.
3. **Chat UI State**: Submitting a query adds a loading state, disables the input, and eventually displays the AI response with evidence cards.
4. **Responsiveness**: The grid layout adapts gracefully to smaller laptop screens and tablets.

### ⚠️ Edge Cases & Boundary Conditions
1. **Backend Offline**: The frontend must gracefully handle `fetch` failures (e.g., showing a "Backend unreachable" toast rather than crashing).
2. **Empty States**: Navigating to the Opportunity Map before any data has been ingested or processed (should show empty placeholders).
3. **Long Strings**: Theme names or user quotes that are extremely long break the flexbox/grid layout (requires `truncate` or `break-words`).
4. **Hydration Mismatches**: Next.js server-rendered HTML differing from client-rendered HTML due to timezone differences in dates.

---

## Phase 6: Pipeline Scheduling & Monitoring

### 🧪 Test Cases (Expected Behavior)
1. **Cron Triggers**: `APScheduler` successfully fires the ingestion job at 2 AM UTC on Sunday.
2. **Auto-Start**: The scheduler starts seamlessly alongside the FastAPI application lifespan.
3. **Health Alerts**: The `MonitoringService` accurately detects if the classification failure rate exceeds the 5% threshold.
4. **Manual Override**: `POST /api/pipeline/trigger/ingest_all_sources` manually starts a background job.

### ⚠️ Edge Cases & Boundary Conditions
1. **Job Overlap**: The scraping job takes 30 minutes, but is scheduled every 15 minutes, causing parallel executions that duplicate data or lock the database.
2. **Multi-Worker Environments**: If deploying 3 instances of the FastAPI app (e.g., in Kubernetes), the cron jobs will fire 3 times simultaneously (requires a distributed lock like Redis or a dedicated worker node).
3. **Silent Failures**: A job crashes silently due to an unhandled exception, failing to update its status in the `pipeline_runs` table.
4. **Clock Skew**: Server time is out of sync, causing jobs to fire at unexpected times.

---

## Phase 7: Deployment, Auth & Polish

### 🧪 Test Cases (Expected Behavior)
1. **Docker Builds**: Multi-stage Dockerfiles for both frontend and backend build successfully without unnecessary bloat.
2. **Env Injection**: Vercel successfully injects the `NEXT_PUBLIC_API_URL` during the frontend build.
3. **Startup Script**: `python scripts/setup.py --all` executes end-to-end without errors on a fresh machine.
4. **Production Startup**: The Railway deployment automatically runs `alembic upgrade head` before starting `uvicorn`.

### ⚠️ Edge Cases & Boundary Conditions
1. **OOM Kills (Out of Memory)**: The Playwright scraper consumes too much RAM on the deployment container, causing the platform to kill the process.
2. **Missing System Dependencies**: The backend Docker container fails because it is missing shared libraries required by Playwright (e.g., `libgobject`).
3. **Platform Architecture**: Building the Docker image on an Apple Silicon (ARM64) Mac but deploying to an AMD64 server without using `--platform linux/amd64`, resulting in an `exec format error`.
4. **Stale Build Cache**: Next.js aggressively caches fetch requests, causing the production dashboard to show stale data until revalidated.
