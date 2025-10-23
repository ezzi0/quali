# Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTAKE CHANNELS                          │
│  Web Chat  │  WhatsApp Flow  │  Meta Lead Ads  │  Future: SMS  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Webhooks   │  │   REST API   │  │  SSE Stream  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OpenAI Agent Layer                          │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  GPT-4 + Tools (inventory_search, normalize_budget)  │      │
│  │  Structured Output: LeadQualification                │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
        ┌───────────────────┐    ┌───────────────────┐
        │    PostgreSQL     │    │      Qdrant       │
        │  (Structured Data)│    │  (Vector Search)  │
        └───────────────────┘    └───────────────────┘
                    │
                    ▼
        ┌───────────────────┐
        │    Redis Queue    │
        │  (Background Jobs)│
        └───────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Lead Inbox   │  │ Lead Detail  │  │   Pipeline   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Lead Intake
```
User Message → Webhook/API → Create/Update Lead → Enqueue Agent Job
```

### 2. Agent Qualification
```
Agent Receives Message
  ↓
Calls Tools:
  - inventory_search(criteria) → Qdrant semantic search
  - normalize_budget(text) → Parse budget range
  - geo_match(city, areas) → Validate locations
  - lead_score(profile) → Calculate 0-100 score
  ↓
Generate LeadQualification (Structured Output)
  ↓
Persist to Postgres → Update Lead Status
```

### 3. Scoring Algorithm (Transparent)
```
Fit Score (40%)
  ├─ Location match (20%)
  └─ Property type/beds/size (20%)

Budget Alignment (25%)
  └─ Matches within budget range

Intent & Urgency (20%)
  ├─ Timeline (12%)
  └─ Specificity (8%)

Readiness (15%)
  ├─ Contact validity (8%)
  └─ Pre-approval status (7%)

─────────────────────
Total: 0-100 score
Qualified if ≥ 60
```

## Database Schema

### Core Entities
- **contacts**: Person details (name, email, phone, consents)
- **leads**: Sales opportunities (source, persona, status, contact_id)
- **lead_profiles**: Requirements (city, areas, type, beds, budget, timeline)
- **qualifications**: AI results (score, qualified, reasons, next_step, top_matches)
- **units**: Inventory (price, location, beds, area_m2, features)
- **activities**: Timeline (message, note, call, status_change)
- **tasks**: Follow-ups (title, due_at, assignee, status)
- **sessions**: Chat sessions (channel, session_key, last_seen)

### Indexes
```sql
-- Leads
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX idx_leads_status ON leads(status);

-- Units
CREATE INDEX idx_units_location ON units(location);
CREATE INDEX idx_units_type_beds ON units(property_type, beds);
CREATE INDEX idx_units_price ON units(price);
CREATE GIN INDEX idx_units_features ON units USING GIN(features);

-- Qualifications
CREATE INDEX idx_qual_score ON qualifications(score DESC, created_at DESC);
```

## Vector Store (Qdrant)

### Collections

#### 1. `units` Collection
- **Purpose**: Semantic search over inventory
- **Vector Dim**: 1536 (OpenAI text-embedding-3-small)
- **Distance**: Cosine
- **Payload**: unit_id, title, price, beds, location, property_type

#### 2. `lead_memories` Collection
- **Purpose**: Per-lead conversation context
- **Vector Dim**: 1536
- **Distance**: Cosine
- **Payload**: lead_id, message, timestamp, speaker

## API Endpoints

### Leads
```
GET    /leads                List leads (filters: status, limit, offset)
GET    /leads/:id            Lead detail + timeline
POST   /leads/:id/tasks      Create follow-up task
POST   /leads/:id/qualify    Manual qualification override
```

### Inventory
```
GET    /inventory/search     Search units (city, type, beds, price range)
GET    /inventory/:id        Unit details
```

### Agent
```
POST   /agent/turn           Process message (SSE streaming)
POST   /agent/session        Create chat session
```

### Webhooks
```
POST   /webhooks/leadads     Meta Lead Ads webhook
POST   /webhooks/whatsapp    WhatsApp webhook (messages + Flows)
```

## Authentication

### MVP (No-Auth)
- Optional `X-API-Secret` header check
- Assumes upstream platform handles auth
- Future: JWT tokens, role-based access (admin/agent)

## Observability

### Logging
- **Format**: Structured JSON (structlog)
- **Fields**: request_id, timestamp, level, event, context
- **PII Redaction**: Email, phone, SSN patterns

### Metrics (Future)
- Request duration (p50, p95, p99)
- Agent tool call counts
- Qualification score distribution
- Lead conversion funnel

### Tracing (Future)
- OpenTelemetry integration
- Trace agent decisions end-to-end

## Deployment

### Local Development
```bash
make setup    # Initialize env, install deps
make dev      # Start all services with Docker Compose
```

### Production (Render)
- **API**: Docker service (FastAPI + Uvicorn)
- **Web**: Node service (Next.js SSR)
- **Qdrant**: Private service with persistent disk
- **Redis**: Managed Redis (starter plan)
- **Postgres**: Managed PostgreSQL (starter plan)

### CI/CD
- **CI**: GitHub Actions (lint, test, build)
- **CD**: Auto-deploy on push to `main` (Render Blueprint)

## Scaling Considerations

### Current Bottlenecks
1. OpenAI API rate limits
2. Synchronous agent calls

### Future Optimizations
1. **Prompt Caching**: Cache system prompts (reduce tokens by 50%)
2. **Batch Embeddings**: Embed units in batches
3. **Read Replicas**: Postgres read replica for reports
4. **Redis Queue**: Async agent qualification
5. **Rate Limiting**: Per-contact rate limits (prevent spam)

### Horizontal Scaling
- API: Stateless, scale to N instances
- Workers: Scale background job consumers
- Qdrant: Cluster mode (if needed)

## Security

### Data Protection
- PII redaction in logs
- Encrypt sensitive fields at rest (future)
- HTTPS/TLS for all communication

### Webhook Verification
- Meta webhook signature verification
- Idempotency keys for webhooks

### GDPR/DSR
- Export endpoint: `/leads/:id/export`
- Delete endpoint: `/leads/:id/delete` (soft delete)
- Retention policy: 2 years (configurable)

## AI Safety

### Guardrails
- Step limit: Max 10 tool calls per turn
- Time limit: 60s timeout
- Fallback: Human handoff if stuck
- Output validation: Pydantic schemas

### Evals (Future)
```python
# tests/evals/test_qualification.py
def test_qualified_buyer():
    lead = create_test_lead(persona="buyer", budget=200k, location="Dubai Marina")
    result = agent.qualify(lead)
    assert result.qualified == True
    assert result.score >= 70
```

## Next Steps (Roadmap)

### Phase 1: MVP (Current)
- ✅ Basic CRUD
- ✅ Agent tools & scoring
- ✅ Qdrant integration
- ✅ Next.js UI
- 🚧 Full Agent SDK integration
- 🚧 Chat UI with SSE

### Phase 2: Production Ready
- Pipeline/Kanban view
- WhatsApp Flow integration
- Lead deduplication
- Calendar integration (viewing scheduling)
- Email notifications
- Evals framework

### Phase 3: Advanced
- Multi-agent orchestration (qualifier → negotiator → scheduler)
- Prompt caching + context pruning
- A/B testing framework
- Analytics dashboard
- Mobile app (React Native)

