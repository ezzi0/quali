# Real Estate AI CRM

AI-powered lead qualification system for real estate with FastAPI, Next.js, Qdrant, and OpenAI.

## Architecture

### Backend (FastAPI + Python 3.12)
- **API**: REST endpoints + SSE streaming for agent
- **Database**: PostgreSQL (SQLAlchemy + Alembic)
- **Vector DB**: Qdrant (embeddings for units and conversations)
- **AI**: OpenAI (GPT-4 + Embeddings)
- **Queue/Cache**: Redis
- **Auth**: No-auth MVP (optional secret header)

### Frontend (Next.js 15 + TypeScript)
- **Pages**: Lead Inbox, Lead Detail, Inventory, Pipeline
- **Features**: SSE streaming chat, real-time updates
- **Styling**: Inline CSS (easily swappable for Tailwind)

### Infrastructure
- **Dev**: Docker Compose
- **Prod**: Render (web services + private services + disks)
- **CI**: GitHub Actions

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 22+
- Docker & Docker Compose
- OpenAI API key

### Local Development

1. **Clone and setup environment**
```bash
cd apps/api
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

2. **Start infrastructure with Docker Compose**
```bash
cd infra
docker-compose -f docker-compose.dev.yml up -d postgres qdrant redis
```

3. **Run migrations and seed data**
```bash
cd ../apps/api
pip install -r requirements.txt
alembic upgrade head
python -m app.workers.seed_data
python -m app.workers.embed_units
```

4. **Start API**
```bash
uvicorn app.main:app --reload
# API runs on http://localhost:8000
```

5. **Start Frontend**
```bash
cd ../web
npm install
npm run dev
# Web runs on http://localhost:3000
```

### Using Docker Compose (Full Stack)

```bash
cd infra
docker-compose -f docker-compose.dev.yml up
```

This starts:
- PostgreSQL (5432)
- Qdrant (6333)
- Redis (6379)
- API (8000)
- Web (3000)

## Project Structure

```
/apps
  /api              # FastAPI backend
    app/
      models/       # SQLAlchemy models
      routes/       # API endpoints
      services/     # Business logic & tools
      workers/      # Background jobs
    alembic/        # Database migrations
  /web              # Next.js frontend
    app/            # App Router pages
/packages
  /schemas          # Shared Pydantic models
  /clients          # API clients (Python & TS)
/infra
  docker-compose.dev.yml
  render.yaml       # Production deployment
```

## API Endpoints

### Leads
- `GET /leads` - List leads with filters
- `GET /leads/:id` - Get lead detail + timeline
- `POST /leads/:id/tasks` - Create follow-up task
- `POST /leads/:id/qualify` - Manual qualification

### Inventory
- `GET /inventory/search` - Search units with filters
- `GET /inventory/:id` - Unit details

### Agent
- `POST /agent/turn` - Process message (SSE stream)
- `POST /agent/session` - Create chat session

### Webhooks
- `POST /webhooks/leadads` - Meta Lead Ads webhook
- `POST /webhooks/whatsapp` - WhatsApp webhook

## Database Schema

Key tables:
- `contacts` - Contact information
- `leads` - Lead opportunities
- `lead_profiles` - Lead requirements
- `qualifications` - AI qualification results
- `units` - Inventory
- `activities` - Timeline events
- `tasks` - Follow-up tasks
- `sessions` - Chat sessions

## Scoring System

Lead scoring (0-100) breakdown:
- **Fit** (40%): Location, type, beds/size match
- **Budget** (25%): Budget alignment with inventory
- **Intent** (20%): Timeline urgency and specificity
- **Readiness** (15%): Contact validity, pre-approval

Qualified threshold: 60+

## Deployment (Render)

1. **Connect GitHub repo to Render**

2. **Set environment variables**:
   - `OPENAI_API_KEY` (required)
   - `APP_SECRET` (optional)

3. **Deploy**:
```bash
# Render auto-deploys from render.yaml
git push origin main
```

Services:
- `realestate-api` - FastAPI (Docker)
- `realestate-web` - Next.js (Node)
- `qdrant` - Private service with disk
- `app-redis` - Redis cache
- `app-postgres` - PostgreSQL database

## Development Commands

### Backend
```bash
# Lint
ruff check .

# Format
ruff format .

# Test
pytest

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Seed data
python -m app.workers.seed_data
python -m app.workers.embed_units
```

### Frontend
```bash
# Lint
npm run lint

# Build
npm run build

# Type check
tsc --noEmit
```

## Features

### ✅ Implemented
- Lead management (CRUD, timeline, tasks)
- Inventory search with filters
- AI tools (inventory search, budget normalization, scoring)
- Qdrant vector store with embeddings
- SSE streaming for agent responses
- Webhook handlers (Lead Ads, WhatsApp)
- Clean UI (Inbox, Lead Detail)
- Docker Compose dev environment
- Render production blueprint
- GitHub Actions CI

### 🚧 Next Steps
1. Full OpenAI Agents SDK integration
2. Chat UI component with SSE
3. Pipeline/Kanban view
4. Lead dedupe logic
5. WhatsApp Flow integration
6. Calendar integration for viewings
7. Evals framework
8. Prompt caching optimization

## License

MIT

