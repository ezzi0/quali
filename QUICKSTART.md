# Quick Start Guide

Get the Real Estate AI CRM running in under 10 minutes.

## Prerequisites

- Python 3.12+
- Node.js 22+
- Docker & Docker Compose
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

## Option 1: Automated Setup (Recommended)

```bash
# 1. Clone/navigate to the project
cd quali

# 2. Run setup script
make setup

# 3. Add your OpenAI API key
# Edit apps/api/.env and add:
# OPENAI_API_KEY=sk-...

# 4. Start everything with Docker Compose
make dev
```

Visit:
- **API**: http://localhost:8000
- **Web UI**: http://localhost:3000
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## Option 2: Manual Setup

### Step 1: Environment Files

```bash
# API
cp apps/api/.env.example apps/api/.env
# Add your OPENAI_API_KEY to apps/api/.env

# Web
cp apps/web/.env.example apps/web/.env
```

### Step 2: Start Infrastructure

```bash
cd infra
docker-compose -f docker-compose.dev.yml up -d postgres qdrant redis
```

### Step 3: Setup Backend

```bash
cd ../apps/api

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed sample data
python -m app.workers.seed_data

# Embed units to Qdrant
python -m app.workers.embed_units

# Start API
uvicorn app.main:app --reload
```

API runs on http://localhost:8000

### Step 4: Setup Frontend

```bash
cd ../web

# Install dependencies
npm install

# Start dev server
npm run dev
```

Web runs on http://localhost:3000

## Verify Installation

### 1. Check API Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "environment": "development"}
```

### 2. List Units

```bash
curl http://localhost:8000/inventory/search | jq
```

Should return 8 sample units.

### 3. List Leads

```bash
curl http://localhost:8000/leads | jq
```

Initially empty (no leads yet).

### 4. Test Web UI

1. Open http://localhost:3000
2. You should see the **Lead Inbox** (empty initially)
3. Click "Inventory" to see sample units

## Create Your First Lead

### Via API

```bash
curl -X POST http://localhost:8000/webhooks/leadads \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "leadgen_id": "test-123",
          "form_data": {
            "field_data": [
              {"name": "full_name", "values": ["John Doe"]},
              {"name": "email", "values": ["john@example.com"]},
              {"name": "phone_number", "values": ["+971501234567"]}
            ]
          }
        }
      }]
    }]
  }'
```

Now refresh http://localhost:3000 and you'll see your first lead!

## Test Agent Chat (Simple)

```bash
curl -X POST http://localhost:8000/agent/turn \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am looking for a 2-bedroom apartment in Dubai Marina with a budget of 150k AED",
    "lead_id": null
  }'
```

This will stream back agent responses.

## Common Issues

### Port Already in Use

If ports 5432, 6333, 6379, 8000, or 3000 are taken:

```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or change ports in docker-compose.dev.yml and .env files
```

### Migration Errors

```bash
# Reset database
make reset-db

# Or manually
cd apps/api
alembic downgrade base
alembic upgrade head
```

### Qdrant Connection Failed

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Restart Qdrant
docker-compose -f infra/docker-compose.dev.yml restart qdrant
```

### Missing OpenAI Key

```
Error: "OPENAI_API_KEY not set"
```

Solution: Add `OPENAI_API_KEY=sk-...` to `apps/api/.env`

## Next Steps

1. **Explore the UI**
   - Lead Inbox: http://localhost:3000
   - Create a lead and view the detail page

2. **Test the API**
   - API Docs: http://localhost:8000/docs (FastAPI auto-docs)
   - Try creating tasks, searching inventory

3. **Read the Architecture**
   - See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed design
   - See [README.md](./README.md) for full documentation

4. **Build a Chat UI**
   - Integrate the `/agent/turn` SSE endpoint
   - Stream responses to a chat component

5. **Deploy to Production**
   - Push to GitHub
   - Connect to Render
   - Auto-deploys via `render.yaml`

## Useful Commands

```bash
# Development
make dev          # Start all services
make api          # Start API only
make web          # Start web only

# Testing
make test         # Run tests
make lint         # Run linters

# Database
make reset-db     # Reset and reseed database

# Cleanup
make clean        # Stop and remove containers
```

## Getting Help

- Check [README.md](./README.md) for detailed docs
- Review [ARCHITECTURE.md](./ARCHITECTURE.md) for system design
- Check API docs: http://localhost:8000/docs
- Review logs:
  ```bash
  # API logs
  docker logs quali-api
  
  # Database logs
  docker logs quali-postgres
  ```

## What's Next?

Now that you have the system running:

1. **Customize the Agent**
   - Edit `apps/api/app/routes/agent.py`
   - Add more tools in `apps/api/app/services/tools.py`

2. **Improve Scoring**
   - Adjust weights in `apps/api/app/services/scoring.py`
   - Add new scoring factors

3. **Build Features**
   - Pipeline/Kanban view
   - Chat UI component
   - WhatsApp integration
   - Email notifications

4. **Add Tests**
   - Write evals for agent quality
   - Add integration tests

Happy building! 🚀

