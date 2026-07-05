# TECHNICAL PRODUCT SPECIFICATION
## AI-Powered Review Discovery Engine
## Spotify Growth Team — Music Discovery Intelligence Platform

**Document Type**: Production System Specification  
**Target Platform**: Google Antigravity (AI Coding Assistant)  
**Version**: 1.0  
**Status**: Ready for Build  

---

## 1. SYSTEM OVERVIEW

### 1.1 Purpose

Build a production-grade, AI-powered intelligence system that ingests unstructured user feedback from multiple public sources — App Store reviews, Play Store reviews, Reddit discussions, community forums, and social media — and converts them into structured, queryable product intelligence via an interactive PM dashboard.

The system answers one core product question:

> **"Why do Spotify users with intent to discover new music still end up listening to the same familiar content repeatedly — and what unmet needs are driving this behavior?"**

This is not a generic sentiment analysis tool. It is a discovery-specific research intelligence engine designed to serve a Product Manager on Spotify's Growth Team as a primary research instrument, replacing weeks of manual review reading with minutes of natural-language querying.

---

### 1.2 Problem Context

Spotify has acquired hundreds of millions of users and operates one of the most sophisticated music recommendation systems in the world. Despite this, a significant and measurable percentage of total listening time comes from:

- Repeat playlists the user has listened to many times before
- Familiar artists the user has known for years
- Previously discovered tracks the user has saved or streamed repeatedly

Spotify's behavioral data (skip rates, stream counts, session lengths, playlist completion rates) tells the Growth Team **what** users are doing. It does not tell them **why** users default to repetition even when they have stated intent to discover new music.

Meanwhile, users are generating millions of data points of explicit qualitative signal in public channels — App Store reviews, Reddit threads, community forums, social media — that directly explain their frustrations, motivations, and unmet needs. This signal exists at scale but is:

- Unstructured (free text, no tagging)
- Distributed across five+ sources
- Impossible to analyze manually at the volume and speed required
- Currently unused for structured product decision-making

**The system built here bridges that gap.**

---

### 1.3 Who Uses This System

**Primary User**: Product Manager, Spotify Growth Team  
**Use Cases**:
- Pre-interview research: "What are the top 5 complaints about Discover Weekly in the last 90 days?"
- Hypothesis validation: "Do power users complain differently about recommendations than new users?"
- Opportunity sizing: "Which unmet needs appear across 3 or more sources consistently?"
- Segment identification: "Which reviews suggest the user wants to discover but keeps repeating?"
- Deck preparation: "Give me the 3 most representative quotes per theme"

**Secondary User**: UX Researcher, Data Analyst  
**Use Cases**: Cross-source trend reports, segment behavioral analysis, longitudinal complaint tracking

---

## 2. SYSTEM ARCHITECTURE

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION LAYER                     │
│  App Store │ Play Store │ Reddit │ Forums │ Social Media        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE LAYER                         │
│  Scraping → Cleaning → Deduplication → Normalization            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI PROCESSING LAYER                        │
│  Classification → Tagging → Clustering → Synthesis              │
│  (Claude API / GPT-4 API)                                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       STORAGE LAYER                             │
│  Structured Database (PostgreSQL or Supabase)                   │
│  Vector Store for semantic search (Pinecone or pgvector)        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER (RAG)                     │
│  Natural Language Query Engine over structured + vector data    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DASHBOARD LAYER                           │
│  PM-facing interactive UI: Theme Explorer, Query Interface,     │
│  Segment Breakdown, Quote Library, Opportunity Map              │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2.2 Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | Python 3.11+ (FastAPI) | Async support, clean API design |
| AI Processing | Claude API (claude-sonnet-4-6) or GPT-4o | Instruction-following for structured classification |
| Vector Store | pgvector (PostgreSQL extension) or Pinecone | Semantic similarity search over review embeddings |
| Embeddings | text-embedding-3-small (OpenAI) or Claude Embeddings | Convert reviews to vectors for clustering |
| Database | PostgreSQL (Supabase for managed hosting) | Structured storage of tagged reviews |
| Scraping | Python (Playwright + BeautifulSoup + PRAW for Reddit) | Multi-source ingestion |
| Frontend | Next.js 14 + Tailwind CSS | Fast, responsive PM dashboard |
| Deployment | Vercel (frontend) + Railway or Render (backend) | Production-grade, low ops overhead |
| Scheduling | Cron jobs (Railway) or GitHub Actions | Automated refresh of data pipeline |
| Auth | Clerk or Supabase Auth | Secure PM access |

---

## 3. DATA INGESTION LAYER

### 3.1 Source 1 — Apple App Store Reviews

**Target**: Spotify app reviews (App ID: 324684580)  
**Method**: Use the iTunes RSS API (public, no auth required) + supplement with third-party review scraping library (`app-store-scraper` Python package)  
**Fields to capture**:

```json
{
  "source": "app_store",
  "review_id": "string",
  "rating": "integer (1-5)",
  "title": "string",
  "body": "string (full review text)",
  "author": "string (anonymized/hashed)",
  "date": "ISO 8601 datetime",
  "version": "string (app version reviewed)",
  "country": "string (ISO country code)",
  "helpful_votes": "integer (if available)",
  "raw_url": "string"
}
```

**Volume target**: 1,000+ reviews minimum, prioritizing 1-3 star reviews (highest signal for frustrations) and recency (last 12 months)  
**Refresh cadence**: Weekly automated pull  
**Rate limiting**: Respect Apple RSS limits; implement exponential backoff

---

### 3.2 Source 2 — Google Play Store Reviews

**Target**: Spotify app reviews (package: com.spotify.music)  
**Method**: `google-play-scraper` Python package  
**Fields to capture**:

```json
{
  "source": "play_store",
  "review_id": "string",
  "rating": "integer (1-5)",
  "body": "string",
  "author": "string (anonymized/hashed)",
  "date": "ISO 8601 datetime",
  "thumbs_up_count": "integer",
  "app_version": "string",
  "reply_content": "string (developer reply if present)",
  "reply_date": "ISO 8601 datetime",
  "raw_url": "string"
}
```

**Volume target**: 1,000+ reviews minimum  
**Priority**: Sort by relevance AND recency; both 1-2 star (frustration) and 4-5 star with discovery mentions  
**Refresh cadence**: Weekly

---

### 3.3 Source 3 — Reddit Discussions

**Target Subreddits**:
- r/spotify (primary — direct product feedback)
- r/Music (contextual — general music discovery behavior)
- r/ifyoulikeblank (behavioral — discovery-seeking behavior)
- r/SpotifyPlaylists (contextual — playlist and discovery behavior)
- r/audiophile (niche — quality-focused discovery segment)

**Method**: Reddit API via PRAW (Python Reddit API Wrapper)  
**Search queries to run**:
- "discover weekly not working"
- "spotify recommendations same songs"
- "sick of same music spotify"
- "can't find new music spotify"
- "spotify algorithm broken"
- "discover weekly stale"
- "release radar useless"
- "spotify keeps repeating"
- "how to discover new music spotify"
- "spotify used to recommend better"

**Fields to capture**:

```json
{
  "source": "reddit",
  "post_id": "string",
  "subreddit": "string",
  "post_title": "string",
  "post_body": "string",
  "post_score": "integer",
  "post_upvote_ratio": "float",
  "post_date": "ISO 8601 datetime",
  "comment_id": "string",
  "comment_body": "string",
  "comment_score": "integer",
  "comment_date": "ISO 8601 datetime",
  "author": "string (anonymized/hashed)",
  "flair": "string",
  "url": "string"
}
```

**Volume target**: 500+ posts + top comments (score > 5)  
**Note**: Capture both the post AND top 10 comments per post — comments often contain richer behavioral signal than the post itself  
**Refresh cadence**: Weekly

---

### 3.4 Source 4 — Spotify Community Forums

**Target**: community.spotify.com  
**Method**: Playwright-based web scraper (JavaScript-rendered content)  
**Target sections**:
- "Music Recommendations" board
- "Discover Weekly" threads
- "Suggestions" board filtered by music discovery
- Any pinned threads about algorithm/recommendation feedback

**Fields to capture**:

```json
{
  "source": "spotify_community",
  "thread_id": "string",
  "thread_title": "string",
  "thread_body": "string",
  "post_date": "ISO 8601 datetime",
  "reply_count": "integer",
  "kudos_count": "integer",
  "status": "string (e.g. 'Not Right Now', 'Under Consideration')",
  "replies": [
    {
      "reply_id": "string",
      "body": "string",
      "date": "ISO 8601 datetime",
      "kudos": "integer"
    }
  ],
  "url": "string"
}
```

**Volume target**: 200+ threads with replies  
**Refresh cadence**: Bi-weekly (slower-moving source)

---

### 3.5 Source 5 — Social Media (Twitter/X)

**Target**: Public posts mentioning Spotify discovery/recommendation issues  
**Method**: Twitter/X API v2 (Basic tier) or Apify Twitter scraper if API access is restricted  
**Search queries**:
- "spotify recommend same songs"
- "spotify discover weekly boring"
- "spotify algorithm bad"
- "can't find new music spotify"
- "spotify used to be better at recommendations"
- "@spotify discover weekly"
- "spotify playlist repetitive"

**Fields to capture**:

```json
{
  "source": "twitter_x",
  "tweet_id": "string",
  "text": "string",
  "author_id": "string (anonymized/hashed)",
  "created_at": "ISO 8601 datetime",
  "like_count": "integer",
  "retweet_count": "integer",
  "reply_count": "integer",
  "lang": "string",
  "url": "string"
}
```

**Volume target**: 500+ posts  
**Filter**: English language only (en); exclude retweets for deduplication  
**Refresh cadence**: Weekly  
**Fallback**: If Twitter/X API is unavailable or cost-prohibitive, use Apify's Twitter Scraper actor as an alternative ingestion method

---

### 3.6 Data Pipeline — Cleaning and Normalization

After ingestion from all sources, run the following processing steps before AI classification:

**Step 1: Deduplication**
- Hash each text body (MD5 or SHA-256)
- Remove exact duplicates within and across sources
- Flag near-duplicates (Jaccard similarity > 0.85) for review

**Step 2: Language Filtering**
- Detect language using `langdetect` library
- Keep only English-language entries for this version (v1.0)
- Store non-English entries in a separate table for future multilingual expansion

**Step 3: Relevance Filtering**
- Run a lightweight keyword pre-filter to remove clearly irrelevant entries (e.g., reviews about billing, login issues, app crashes that have zero discovery mention)
- Keyword relevance list: ["discover", "recommend", "suggestion", "new music", "playlist", "algorithm", "same song", "repeat", "explore", "find music", "discover weekly", "release radar", "radio", "similar", "boring", "stale", "tired of"]
- Entries with zero keyword matches → move to `excluded` table with reason flag
- Entries with 1+ keyword match → proceed to AI classification

**Step 4: Text Normalization**
- Strip HTML tags, special characters, excess whitespace
- Truncate entries exceeding 2,000 characters (keep first 2,000; store full text separately)
- Anonymize any personally identifiable information (usernames replaced with hashed IDs)

**Step 5: Metadata Enrichment**
- Add `processed_at` timestamp
- Add `source_weight` score (App Store/Play Store = 1.0; Reddit = 0.9; Forums = 0.8; Social = 0.7) for downstream confidence scoring
- Add `recency_score` (last 30 days = 1.0; 31-90 days = 0.8; 91-180 days = 0.6; 180+ days = 0.4)

---

## 4. AI PROCESSING LAYER

### 4.1 Primary Classification Prompt

For each cleaned entry, send the following structured prompt to the AI model:

```
SYSTEM:
You are a product research analyst at Spotify working on the Growth Team.
Your job is to classify user feedback to understand why users struggle to discover new music.
You must respond ONLY with a valid JSON object. No preamble, no explanation, no markdown.

USER:
Analyze the following user feedback and return a JSON object with these exact fields:

INPUT TEXT:
"{text}"

SOURCE: {source}
RATING (if available): {rating}

REQUIRED OUTPUT JSON:
{
  "is_discovery_relevant": true/false,
  "primary_complaint_category": "one of: [algorithm_staleness, choice_overload, trust_erosion, mood_mismatch, interface_friction, lack_of_context, genre_bubble, social_disconnect, no_complaint, other]",
  "secondary_complaint_category": "same options as above or null",
  "user_segment_signal": "one of: [active_explorer_stuck, background_listener, mood_regulator, identity_listener, socially_led_discoverer, new_user, unclear]",
  "sentiment": "one of: [very_negative, negative, neutral, positive, very_positive]",
  "sentiment_score": float between -1.0 and 1.0,
  "discovery_intent": "one of: [high, medium, low, none]",
  "repetition_behavior_mentioned": true/false,
  "key_frustration_phrase": "string — the single most important phrase from the text that captures the core frustration, or null",
  "unmet_need": "string — a concise (max 15 words) statement of what the user actually wants but isn't getting, or null",
  "jtbd_statement": "string — complete this: 'When [situation], I want [need], so that [outcome]' based on this text, or null",
  "confidence_score": float between 0.0 and 1.0,
  "language": "ISO 639-1 language code"
}

CLASSIFICATION DEFINITIONS:
- algorithm_staleness: User feels recommendations don't change or improve over time
- choice_overload: User feels overwhelmed by too many options or can't decide what to try
- trust_erosion: User tried recommendations, didn't like them, stopped trusting the system
- mood_mismatch: Recommendations don't match the user's current mood or context
- interface_friction: Discovery surfaces are hard to find, navigate, or use
- lack_of_context: Algorithm doesn't understand WHY the user listens to certain songs (context collapse)
- genre_bubble: Algorithm is too narrow, keeps user in one genre/era/artist cluster
- social_disconnect: User discovers music through humans/social media, not the algorithm
- no_complaint: Text is positive or neutral with no frustration signal
- other: Frustration present but doesn't fit above categories

USER SEGMENT DEFINITIONS:
- active_explorer_stuck: User wants to discover new music but keeps repeating familiar content
- background_listener: Music is functional/background; discovery is not important to them
- mood_regulator: Uses music to achieve a specific emotional state; new music is risky
- identity_listener: Music reflects identity/nostalgia; discovery irrelevant to their job
- socially_led_discoverer: Discovers through friends/social, not algorithm
- new_user: Recently joined, still building library
- unclear: Cannot determine segment from text
```

**Model**: claude-sonnet-4-6 (primary) with GPT-4o as fallback  
**Temperature**: 0.1 (low randomness — classification task)  
**Max tokens**: 500  
**Batch size**: Process 50 entries per batch to manage rate limits  
**Error handling**: If JSON parse fails, retry once with explicit JSON-only instruction; if second attempt fails, flag entry as `classification_failed` and log for manual review

---

### 4.2 Theme Clustering

After individual classification, run a second-pass clustering to identify macro-themes across all classified entries:

**Step 1: Embed all `key_frustration_phrase` values** using text-embedding-3-small  
**Step 2: Run k-means clustering** (k=8 initially; adjust based on silhouette score)  
**Step 3: For each cluster, send top 20 representative entries to AI for theme labeling**:

```
SYSTEM: You are a product researcher. Given these user feedback excerpts that have been grouped together, identify the single unifying theme they share. Respond with: {"theme_name": "string (3-5 words)", "theme_description": "string (1 sentence)", "representative_quote": "string (best single quote from the list)"}

USER: Here are {n} user feedback excerpts grouped together:
{list of excerpts}
```

**Step 4: Store cluster ID, theme name, theme description, and representative quote in `themes` table**  
**Step 5: Link each review to its cluster via `review_theme_mapping` table**

---

### 4.3 Cross-Source Synthesis

Daily batch job that runs the following aggregations and stores results in a `synthesis_cache` table:

- Theme frequency by source (how often each theme appears in App Store vs Reddit vs etc.)
- Theme frequency by segment (which segments mention which themes most)
- Theme cross-source score (themes appearing in 3+ sources get `high_confidence` flag)
- Trend direction (is a theme growing or declining over time based on `date` field)
- Top 5 unmet needs by frequency (aggregated from `unmet_need` field across all entries)
- Top representative quotes per theme (highest `source_weight` × `recency_score` × `sentiment_score` magnitude)

---

### 4.4 Embeddings and Vector Store

**Purpose**: Enable semantic search — the PM can ask "show me reviews about the algorithm not understanding my mood" and retrieve relevant entries even if they don't use those exact words.

**Process**:
1. Embed the full `body` text of each entry using text-embedding-3-small
2. Store embedding vector in pgvector column alongside structured fields
3. On query, embed the query string and run cosine similarity search (top-k=20)
4. Return results ranked by similarity score × recency_score × source_weight

---

## 5. DATABASE SCHEMA

### 5.1 Core Tables

```sql
-- Raw ingested reviews (all sources)
CREATE TABLE raw_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source VARCHAR(50) NOT NULL, -- 'app_store', 'play_store', 'reddit', 'spotify_community', 'twitter_x'
  external_id VARCHAR(255) UNIQUE,
  rating INTEGER, -- NULL for sources without ratings
  title TEXT,
  body TEXT NOT NULL,
  author_hash VARCHAR(64),
  published_at TIMESTAMPTZ,
  app_version VARCHAR(50),
  country_code VARCHAR(10),
  engagement_score INTEGER, -- helpful_votes / upvotes / likes depending on source
  raw_url TEXT,
  ingested_at TIMESTAMPTZ DEFAULT NOW(),
  language VARCHAR(10),
  is_relevant BOOLEAN DEFAULT NULL, -- set after relevance filter
  exclusion_reason VARCHAR(255) -- if is_relevant = false
);

-- AI-classified and tagged reviews
CREATE TABLE classified_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_review_id UUID REFERENCES raw_reviews(id),
  is_discovery_relevant BOOLEAN,
  primary_complaint_category VARCHAR(100),
  secondary_complaint_category VARCHAR(100),
  user_segment_signal VARCHAR(100),
  sentiment VARCHAR(50),
  sentiment_score FLOAT,
  discovery_intent VARCHAR(20),
  repetition_behavior_mentioned BOOLEAN,
  key_frustration_phrase TEXT,
  unmet_need TEXT,
  jtbd_statement TEXT,
  confidence_score FLOAT,
  source_weight FLOAT,
  recency_score FLOAT,
  embedding VECTOR(1536), -- pgvector column
  classified_at TIMESTAMPTZ DEFAULT NOW(),
  classification_model VARCHAR(50),
  classification_failed BOOLEAN DEFAULT FALSE
);

-- Clusters / Themes
CREATE TABLE themes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id INTEGER UNIQUE,
  theme_name VARCHAR(255),
  theme_description TEXT,
  representative_quote TEXT,
  review_count INTEGER,
  cross_source_count INTEGER, -- how many distinct sources mention this theme
  confidence_level VARCHAR(20), -- 'high', 'medium', 'low'
  trend_direction VARCHAR(20), -- 'growing', 'stable', 'declining'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Review to theme mapping
CREATE TABLE review_theme_mapping (
  review_id UUID REFERENCES classified_reviews(id),
  theme_id UUID REFERENCES themes(id),
  similarity_score FLOAT,
  PRIMARY KEY (review_id, theme_id)
);

-- Synthesis cache (pre-aggregated for dashboard performance)
CREATE TABLE synthesis_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cache_key VARCHAR(255) UNIQUE, -- e.g. 'theme_frequency_by_source_2025_q2'
  data JSONB,
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ
);

-- PM queries log (for analytics on what PMs search for most)
CREATE TABLE query_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_text TEXT,
  query_embedding VECTOR(1536),
  result_count INTEGER,
  queried_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 6. DASHBOARD LAYER (PM-FACING UI)

### 6.1 Dashboard Overview

The dashboard is a Next.js web application with the following views/pages:

---

### 6.2 View 1 — Intelligence Home (Default Landing)

**Purpose**: Give the PM the most important signals at a glance  
**Components**:

- **Stats bar** (top): Total reviews analyzed | Sources active | Last updated | Date range selector
- **Top Themes Panel**: Top 6 themes ranked by frequency, each showing:
  - Theme name
  - Review count and % of total
  - Cross-source indicator (which sources mention this theme)
  - Trend badge (↑ Growing / → Stable / ↓ Declining)
  - Click to expand → shows representative quotes and segment breakdown
- **Unmet Needs Panel**: Top 5 most common unmet needs (aggregated from `unmet_need` field), displayed as ranked cards
- **Segment Distribution Chart**: Donut or bar chart showing % of reviews per user segment signal
- **Sentiment Overview**: Stacked bar by source showing sentiment distribution

---

### 6.3 View 2 — Natural Language Query Interface

**Purpose**: Let the PM ask anything in plain English and get structured answers  
**UI**: Chat-style interface with query input + structured results below

**Example queries the system must handle**:
- "Why do users stop using Discover Weekly?"
- "Show me the top complaints from users who want to discover but keep repeating"
- "What do Reddit users say about the algorithm that App Store reviewers don't mention?"
- "Give me 5 representative quotes about algorithm staleness"
- "Which unmet need appears most consistently across all sources?"
- "What is the JTBD of users in the active explorer stuck segment?"

**Backend logic**:
1. Embed query → cosine similarity search over `classified_reviews` embeddings
2. Also run structured SQL filter based on NLP-extracted intent (e.g., if query mentions "Reddit", filter `source = 'reddit'`)
3. Send top-k results + query to AI for synthesis:

```
SYSTEM: You are a product research analyst at Spotify. 
Answer the PM's question based ONLY on the provided user feedback data. 
Be specific, cite evidence, and structure your answer clearly.
If the data doesn't contain enough information to answer confidently, say so.

USER QUESTION: {query}

RELEVANT FEEDBACK DATA:
{top_k results as JSON}

Respond with:
1. Direct answer (2-3 sentences)
2. Supporting evidence (3-5 bullet points with source citations)
3. Confidence level (High / Medium / Low) with reason
4. Suggested follow-up questions
```

4. Display AI synthesis + the raw retrieved reviews (expandable) so PM can verify

---

### 6.4 View 3 — Theme Explorer

**Purpose**: Deep-dive into any single theme  
**Components**:
- Theme selector (dropdown of all identified themes)
- For selected theme:
  - Definition and description
  - Review count by source (bar chart)
  - Review count by segment (bar chart)
  - Sentiment breakdown (pie chart)
  - Trend over time (line chart by month)
  - Top 10 representative quotes (with source, date, rating badges)
  - Related themes (by embedding similarity)
  - Raw reviews table (filterable, sortable, with all metadata)

---

### 6.5 View 4 — Segment Breakdown

**Purpose**: Understand how different user segments express the discovery problem  
**Components**:
- Segment selector (all 7 segments)
- For selected segment:
  - Total reviews in segment
  - Top 3 complaint categories (ranked)
  - Top unmet needs (ranked)
  - Sentiment distribution
  - Most representative JTBD statements (top 5)
  - Cross-source presence (which platforms does this segment appear on most)
  - Representative quotes (top 10)

---

### 6.6 View 5 — Opportunity Map

**Purpose**: Help PM prioritize which problems to solve  
**Components**:
- 2x2 matrix visualization:
  - X-axis: Frequency (how often is this problem mentioned)
  - Y-axis: Severity (average negative sentiment score of reviews mentioning this)
  - Bubble size: Cross-source consistency score (how many sources mention it)
  - Color: Segment (which segment does this problem belong to)
- Each bubble = one theme; hover to see theme name, count, top quote
- Click bubble → links to Theme Explorer for that theme

---

### 6.7 View 6 — Quote Library

**Purpose**: PM needs verbatim quotes for decks, interview guides, stakeholder docs  
**Components**:
- Filter panel: Source | Segment | Theme | Sentiment | Date range | Rating
- Results: Paginated list of quotes, each with:
  - Full review body (expandable)
  - Source badge, date, rating, segment tag, theme tag
  - "Copy quote" button (copies formatted quote with source attribution)
  - "Save to collection" button (bookmark for later use)
- Saved Collections: PM can create named collections of quotes (e.g., "Algorithm Staleness Evidence")

---

## 7. API LAYER

### 7.1 Core Endpoints

```
POST   /api/ingest/trigger          → Manually trigger ingestion for one or all sources
GET    /api/reviews                 → List reviews with filters (source, segment, theme, date, sentiment)
GET    /api/reviews/{id}            → Get single review with full classification
POST   /api/query                   → Natural language query (returns AI synthesis + raw results)
GET    /api/themes                  → List all themes with stats
GET    /api/themes/{id}             → Get single theme with full breakdown
GET    /api/segments                → Get all segment summaries
GET    /api/segments/{segment_id}   → Get single segment deep-dive
GET    /api/opportunities           → Get opportunity map data (themes × frequency × severity)
GET    /api/synthesis/summary       → Get top-level intelligence summary (home dashboard data)
GET    /api/quotes                  → Get filtered quotes for Quote Library
POST   /api/collections             → Create a quote collection
PUT    /api/collections/{id}        → Add/remove quotes from collection
GET    /api/health                  → System health check (pipeline status, DB connection, API keys)
```

---

## 8. AUTOMATED PIPELINE SCHEDULING

### 8.1 Jobs

| Job | Frequency | Description |
|---|---|---|
| `ingest_all_sources` | Weekly (Sunday 2am UTC) | Pull new reviews from all 5 sources |
| `classify_new_reviews` | Daily (1am UTC) | Run AI classification on unprocessed entries |
| `update_clusters` | Weekly (Monday 4am UTC) | Re-cluster and re-label themes with new data |
| `refresh_synthesis_cache` | Daily (3am UTC) | Recompute all aggregations for dashboard |
| `embed_new_reviews` | Daily (2am UTC) | Generate and store embeddings for new classified reviews |
| `health_check` | Every 15 minutes | Verify pipeline status; alert on failure |

---

## 9. ERROR HANDLING AND MONITORING

### 9.1 Error States and Responses

| Error | Handling |
|---|---|
| Scraping blocked (429/403) | Exponential backoff (1min → 5min → 15min → skip + log) |
| AI API rate limit | Queue with delay; retry with exponential backoff |
| AI returns invalid JSON | Retry once with stricter prompt; if fails, flag `classification_failed = true` |
| Database write failure | Log to dead-letter queue; retry on next job run |
| Embedding API failure | Mark entry `embedding_pending = true`; retry in next daily job |
| Query returns zero results | Return graceful "not enough data" response with suggested alternative queries |

### 9.2 Monitoring

- Log all pipeline run durations and entry counts to `pipeline_runs` table
- Alert (email or Slack webhook) if:
  - Any ingestion job returns 0 entries
  - Classification failure rate exceeds 5%
  - Dashboard response time exceeds 3 seconds
  - Any API key returns auth error
- Dashboard health indicator (green/yellow/red) visible to PM at top of UI

---

## 10. SECURITY AND COMPLIANCE

- All author identifiers (usernames, Reddit handles, tweet authors) must be hashed before storage — store hash only, never the original identifier
- No personal data stored beyond what is required for research intelligence
- All API keys stored in environment variables, never in code
- Database access restricted to application service account only
- HTTPS enforced on all endpoints
- Rate limiting on all API endpoints (100 requests/minute per authenticated user)
- Dashboard access restricted to authenticated users (Clerk or Supabase Auth)

---

## 11. DELIVERABLE REQUIREMENTS (FELLOWSHIP SPECIFIC)

### 11.1 Live Demo Link

The deployed system must be accessible at a public URL where:
- A reviewer can log in with a demo account (provide credentials in deck)
- The dashboard loads with pre-populated data (minimum 500 analyzed entries)
- The natural language query interface responds within 10 seconds
- At least 5 themes are visible with data
- Segment breakdown is populated with at least 3 segments

### 11.2 Architecture Slide (1 slide in deck)

The single architecture slide must show:
- 5 input sources → pipeline → AI classification → database → dashboard
- Label each major step with the technology used
- Include a sample output (one classified review shown as JSON or card)
- Must be readable at minimum 14pt font (or 26pt if Figma at 1920×1080)

---

## 12. ACCEPTANCE CRITERIA

The system is considered production-ready when all of the following are true:

| Criterion | Pass Condition |
|---|---|
| Data volume | ≥ 500 classified, discovery-relevant entries in database |
| Source coverage | ≥ 3 of 5 sources successfully ingesting |
| Classification accuracy | Manual spot-check of 50 random entries: ≥ 85% classified correctly |
| Theme coherence | ≥ 5 distinct, non-overlapping themes identified with ≥ 20 reviews each |
| Query response time | Natural language query returns result in < 10 seconds |
| Dashboard load time | Home dashboard loads in < 3 seconds |
| Cross-source signal | ≥ 2 themes appear in 3+ sources (high confidence) |
| Segment signal | ≥ 3 user segments distinguishable from data |
| Uptime | System available and responsive during fellowship review window |
| Demo accessibility | Public URL accessible without VPN; demo credentials provided |

---

## 13. OUT OF SCOPE (V1.0)

- Multilingual review analysis (English only in v1.0)
- Real-time streaming ingestion (batch pipeline is sufficient for v1.0)
- Spotify internal behavioral data integration (public sources only)
- Automated interview guide generation (PM does this manually using dashboard output)
- Mobile-responsive dashboard (desktop PM use only in v1.0)
- A/B test result tracking
- Integration with Spotify's internal systems or APIs

---

*End of Specification — v1.0*  
*Ready for ingestion by Google Antigravity AI Coding Assistant*
