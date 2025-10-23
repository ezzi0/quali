# Project Summary: Real Estate AI CRM

## Overview

A production-ready, AI-native CRM for real estate lead qualification built with:
- **Backend**: FastAPI (Python 3.12) + SQLAlchemy + Alembic
- **Frontend**: Next.js 15 (TypeScript, App Router)
- **Vector DB**: Qdrant (embeddings for semantic search)
- **Database**: PostgreSQL (structured data)
- **Cache/Queue**: Redis
- **AI**: OpenAI (GPT-4 + Embeddings)
- **Infrastructure**: Docker Compose (dev) + Render (prod)

## What's Implemented

### ✅ Backend (FastAPI)

#### Core API (`apps/api/app/`)
- **Configuration** (`config.py`): Environment-based settings with Pydantic
- **Logging** (`logging.py`): Structured JSON logs with request IDs and PII redaction
- **Dependencies** (`deps.py`): DB, Qdrant, Redis dependency injection
- **Auth** (`auth.py`): Optional secret header validation (no-auth MVP)

#### Database Models (`apps/api/app/models/`)
- `Contact`: Person details (name, email, phone, consent flags)
- `Lead`: Sales opportunity (source, persona, status, contact_id)
- `LeadProfile`: Requirements (city, areas, type, beds, budget, timeline, financing)
- `Qualification`: AI results (score, qualified, reasons, missing_info, next_step, top_matches)
- `Unit`: Inventory (title, price, area_m2, beds, location, type, features, status)
- `Activity`: Timeline events (message, note, call, status_change)
- `Task`: Follow-up tasks (title, description, due_at, status, assignee)
- `Session`: Chat sessions (channel, session_key, last_seen_at)
- `AuthUser`: User accounts (email, role) - present but unused in MVP

#### API Routes (`apps/api/app/routes/`)

**Leads** (`leads.py`):
- `GET /leads` - List leads with filters (status, limit, offset)
- `GET /leads/:id` - Lead detail with timeline, profile, qualification, tasks
- `POST /leads/:id/tasks` - Create follow-up task
- `POST /leads/:id/qualify` - Manual qualification override (HIL)

**Inventory** (`inventory.py`):
- `GET /inventory/search` - Search units with filters (city, area, type, beds, price)
- `GET /inventory/:id` - Unit details

**Agent** (`agent.py`):
- `POST /agent/turn` - Process message with SSE streaming
- `POST /agent/session` - Create chat session

**Webhooks** (`webhooks.py`):
- `POST /webhooks/leadads` - Meta Lead Ads webhook handler
- `POST /webhooks/whatsapp` - WhatsApp messages + Flow completion handler

#### Services (`apps/api/app/services/`)

**Embedding Store** (`embedding_store.py`):
- `EmbeddingStore` protocol (swappable interface)
- `QdrantEmbeddingStore` implementation
- Collections: `units`, `lead_memories`
- OpenAI embeddings (text-embedding-3-small, dim=1536)

**Scoring** (`scoring.py`):
- Transparent rule-based scoring (0-100)
- Fit (40%): location, type, beds/size match
- Budget (25%): budget alignment with matches
- Intent (20%): timeline urgency + specificity
- Readiness (15%): contact validity + pre-approval
- Qualified threshold: ≥60

**Tools** (`tools.py`):
- `inventory_search(criteria)` → Search units by filters
- `normalize_budget(text)` → Parse budget from text
- `geo_match(city, areas)` → Validate locations
- `lead_score(profile, matches, contact)` → Calculate score
- `persist_qualification(db, lead_id, payload)` → Save to DB

#### Workers (`apps/api/app/workers/`)
- `seed_data.py`: Seed 8 sample units (Dubai properties)
- `embed_units.py`: Embed all units to Qdrant

#### Migrations (`apps/api/alembic/`)
- Initial schema migration: `001_2024_10_22_1200-initial_schema.py`
- Creates all tables with indexes

#### Tests (`apps/api/tests/`)
- `test_scoring.py`: Test scoring logic (high/low quality leads)
- `test_tools.py`: Test budget normalization

### ✅ Frontend (Next.js)

#### Pages (`apps/web/app/`)

**Lead Inbox** (`page.tsx`):
- List all leads with filters (all, new, qualified, viewing, won)
- Table view: ID, contact, source, persona, status, created date
- Status badges with color coding
- Click lead → navigate to detail

**Lead Detail** (`lead/[id]/page.tsx`):
- Contact information card
- Requirements profile (location, type, budget, timeline)
- Qualification card (score, qualified status, reasons, missing info, next step)
- Timeline (all activities)
- Tasks list
- Two-column responsive layout

**Layout** (`layout.tsx`):
- Global layout with metadata
- Header navigation (Leads, Inventory, Pipeline)

### ✅ Shared Schemas (`packages/schemas/`)
- `LeadQualification`: Pydantic model for structured output

### ✅ Infrastructure

#### Docker Compose (`infra/docker-compose.dev.yml`)
- PostgreSQL 16 (port 5432)
- Qdrant (ports 6333, 6334)
- Redis 7 (port 6379)
- API (port 8000)
- Web (port 3000)
- Health checks for all services
- Volumes for persistent data

#### Render Blueprint (`infra/render.yaml`)
- API: Docker web service (FastAPI)
- Web: Node web service (Next.js)
- Qdrant: Private service with 10GB disk
- Redis: Starter plan
- PostgreSQL: Starter plan
- Environment variables wired automatically

#### CI/CD (`.github/workflows/ci.yml`)
- Backend: Python 3.12, ruff lint, pytest, migration check
- Frontend: Node 22, npm lint, build

### ✅ Development Tools

**Makefile**:
- `make setup` - Initialize environment
- `make dev` - Start all services
- `make api` / `make web` - Start individual services
- `make test` - Run tests
- `make lint` - Lint all code
- `make clean` - Clean up containers
- `make reset-db` - Reset database

**Scripts** (`scripts/`):
- `setup_dev.sh` - Automated setup script
- `reset_db.sh` - Database reset script

**Configuration**:
- `ruff.toml` - Python linter config
- `pytest.ini` - Test configuration
- `.gitignore` - Comprehensive ignore rules

## File Tree

```
quali/
├── apps/
│   ├── api/                      # FastAPI backend
│   │   ├── alembic/              # Database migrations
│   │   │   ├── versions/
│   │   │   │   └── 001_..._initial_schema.py
│   │   │   ├── env.py
│   │   │   └── script.py.mako
│   │   ├── alembic.ini
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py           # FastAPI app, middleware, routers
│   │   │   ├── config.py         # Settings (env vars)
│   │   │   ├── deps.py           # Dependency injection
│   │   │   ├── logging.py        # Structured logging + PII redaction
│   │   │   ├── auth.py           # Optional secret header
│   │   │   ├── models/           # SQLAlchemy models
│   │   │   │   ├── base.py
│   │   │   │   ├── contact.py
│   │   │   │   ├── lead.py
│   │   │   │   ├── qualification.py
│   │   │   │   ├── unit.py
│   │   │   │   ├── activity.py
│   │   │   │   ├── task.py
│   │   │   │   ├── session.py
│   │   │   │   └── auth_user.py
│   │   │   ├── routes/           # API endpoints
│   │   │   │   ├── leads.py
│   │   │   │   ├── inventory.py
│   │   │   │   ├── agent.py
│   │   │   │   └── webhooks.py
│   │   │   ├── services/         # Business logic
│   │   │   │   ├── embedding_store.py
│   │   │   │   ├── scoring.py
│   │   │   │   └── tools.py
│   │   │   └── workers/          # Background jobs
│   │   │       ├── seed_data.py
│   │   │       └── embed_units.py
│   │   ├── tests/
│   │   │   ├── test_scoring.py
│   │   │   └── test_tools.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── ruff.toml
│   │   ├── pytest.ini
│   │   └── .env.example
│   └── web/                      # Next.js frontend
│       ├── app/
│       │   ├── layout.tsx        # Root layout
│       │   ├── page.tsx          # Lead Inbox
│       │   ├── globals.css
│       │   └── lead/
│       │       └── [id]/
│       │           └── page.tsx  # Lead Detail
│       ├── public/
│       ├── Dockerfile
│       ├── package.json
│       ├── tsconfig.json
│       ├── next.config.js
│       ├── .eslintrc.json
│       ├── next-env.d.ts
│       └── .env.example
├── packages/
│   ├── schemas/                  # Shared Pydantic models
│   │   ├── __init__.py
│   │   └── qualification.py
│   └── clients/                  # API clients (stubs)
│       ├── python/
│       └── ts/
├── infra/
│   ├── docker-compose.dev.yml    # Local dev environment
│   ├── render.yaml               # Production deployment
│   └── Dockerfile.qdrant
├── scripts/
│   ├── setup_dev.sh
│   └── reset_db.sh
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI
├── Makefile
├── README.md                     # Full documentation
├── QUICKSTART.md                 # 10-min setup guide
├── ARCHITECTURE.md               # System design deep-dive
├── PROJECT_SUMMARY.md            # This file
└── .gitignore
```

## Key Features

### 1. No-Auth MVP
- Optional `X-API-Secret` header
- Designed to be embedded in parent platform
- Easy to add JWT auth later

### 2. Qdrant Vector Search
- Semantic search over units
- Fast local development + production ready
- Swappable interface (can switch to pgvector)

### 3. Transparent Scoring
- Rule-based, explainable scoring (0-100)
- Tunable weights per business needs
- Clear reasons for each score

### 4. AI Tools
- OpenAI function calling ready
- Structured outputs (Pydantic v2)
- SSE streaming for real-time UI

### 5. Production Infra
- Docker Compose for local dev
- Render Blueprint for one-click deploy
- CI/CD with GitHub Actions
- Health checks, migrations, seeding

### 6. Developer Experience
- Makefile commands for common tasks
- Comprehensive README + docs
- Tests for scoring and tools
- Linting (ruff, ESLint)

## What's NOT Implemented Yet

### 🚧 To Be Built (Phase 2)

1. **Full Agent SDK Integration**
   - Current: Simple function calling
   - Needed: Full OpenAI Agents SDK with Runner.stream()

2. **Chat UI Component**
   - Current: API ready with SSE
   - Needed: React component with streaming

3. **Pipeline/Kanban View**
   - Drag-and-drop leads through stages
   - SLA timers per stage

4. **Lead Deduplication**
   - Hash-based email/phone matching
   - AI-suggested merges

5. **WhatsApp Flow Integration**
   - Parse Flow JSON payload
   - Map to LeadProfile fields

6. **Calendar Integration**
   - Schedule viewing tool
   - Google Calendar sync

7. **Evals Framework**
   - Test agent quality
   - Regression tests for scoring

8. **Prompt Caching**
   - Cache system prompts
   - Reduce OpenAI costs by 50%

## Getting Started

See [QUICKSTART.md](./QUICKSTART.md) for 10-minute setup guide.

```bash
# Quick start
make setup
# Add OPENAI_API_KEY to apps/api/.env
make dev
# Visit http://localhost:3000
```

## Deployment

### Local
```bash
make dev
```

### Production (Render)
1. Push to GitHub
2. Connect repo to Render
3. Add `OPENAI_API_KEY` secret
4. Auto-deploys via `render.yaml`

## Tech Stack Summary

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Frontend       | Next.js 15, TypeScript, React 19    |
| Backend        | FastAPI, Python 3.12, Uvicorn       |
| Database       | PostgreSQL 16, SQLAlchemy, Alembic  |
| Vector DB      | Qdrant (Docker)                     |
| Cache/Queue    | Redis 7                             |
| AI             | OpenAI GPT-4o-mini + Embeddings     |
| Dev Infra      | Docker Compose                      |
| Prod Infra     | Render (Blueprint)                  |
| CI/CD          | GitHub Actions                      |
| Logging        | Structlog (JSON)                    |
| Linting        | Ruff (Python), ESLint (TS)          |
| Testing        | pytest, Jest (future)               |

## Project Stats

- **Backend**: ~50 files, ~3000 LOC (Python)
- **Frontend**: ~10 files, ~800 LOC (TypeScript)
- **Infrastructure**: 3 Docker services, 1 Render Blueprint
- **Database**: 9 tables, 15+ indexes
- **API Endpoints**: 12 endpoints
- **Tests**: 4 test cases (expandable)

## License

MIT

## Next Steps

1. Add your OpenAI API key
2. Run `make setup && make dev`
3. Create your first lead via webhook or UI
4. Explore the codebase
5. Build the chat UI
6. Deploy to Render

Happy building! 🚀

