# Marketing Agent Integration Guide

## Overview

This guide explains how the Marketing Agent integrates with your existing Real Estate CRM to create a complete lead generation and qualification system.

**Status**: ✅ **Phase 1 Complete** - Core infrastructure and services implemented

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                             │
│                                                                  │
│  1. User sees ad → 2. Clicks → 3. Lands on site → 4. Qualifies  │
└─────────────────────────────────────────────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                     │
            ▼                    ▼                     ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │   OUTBOUND   │    │   INBOUND    │    │  OPTIMIZE    │
    │   Marketing  │    │ Qualification│    │   & Learn    │
    │    Agent     │    │    Agent     │    │              │
    └──────────────┘    └──────────────┘    └──────────────┘
            │                    │                     │
            │                    │                     │
    ┌───────┴──────────┐ ┌──────┴────────┐  ┌────────┴───────┐
    │ • Personas       │ │ • Chat        │  │ • Attribution  │
    │ • Creatives      │ │ • Scoring     │  │ • Budget Opt   │
    │ • Campaigns      │ │ • RAG         │  │ • A/B Tests    │
    │ • Budget Alloc   │ │ • Tools       │  │ • Analytics    │
    └──────────────────┘ └───────────────┘  └────────────────┘
```

---

## What's Implemented

### ✅ Database Layer

**New Tables:**
- `personas` - Marketing segments with behavioral profiles
- `audiences` - Platform-specific targeting
- `creatives` - AI-generated ad content
- `campaigns` - Multi-platform campaign management
- `ad_sets` - Budget and targeting groups
- `ads` - Individual ad instances
- `experiments` - A/B test configurations
- `marketing_metrics` - Performance tracking

**Extended Tables:**
- `leads` - Added `marketing_persona_id` and `attribution_data`
- `qualifications` - Added `predicted_ltv` and `acquisition_cost`

**Migration:** `002_2024_10_30_1200-marketing_schema.py`

### ✅ Marketing Services

**1. Persona Discovery** (`services/marketing/persona_discovery.py`)
- Uses HDBSCAN clustering on qualified leads
- Extracts features: budget, property type, location, urgency
- LLM-based persona labeling and messaging generation
- Weekly automatic discovery job

**2. Creative Generator** (`services/marketing/creative_generator.py`)
- AI-powered creative generation with GPT-4
- RAG-based brand guidelines integration
- Multi-layer compliance checks (Fair Housing Act)
- Toxicity detection via OpenAI Moderation API
- Generates multiple A/B variants

**3. Budget Optimizer** (`services/marketing/budget_optimizer.py`)
- Thompson Sampling for allocation
- Beta distribution modeling of conversion rates
- Business constraints: floors, ceilings, volatility caps
- Cooldown periods between changes
- Confidence-weighted recommendations

**4. Attribution** (`services/marketing/attribution.py`)
- UTM parameter parsing
- Platform click ID tracking (fbclid, gclid)
- Multi-touch attribution
- Offline conversion formatting for:
  - Meta Conversions API (CAPI)
  - Google Enhanced Conversions
  - TikTok Events API

### ✅ Platform Adapters

**Meta Marketing API** (`adapters/meta_marketing.py`)
- Campaign/AdSet/Ad CRUD
- Creative uploads
- Insights pulling
- Conversions API integration
- Dry-run mode for testing

**Google Ads** (`adapters/google_ads.py`) - Stub
- Interface defined for future implementation

**TikTok Ads** (`adapters/tiktok_ads.py`) - Stub
- Interface defined for future implementation

### ✅ API Endpoints

**Marketing Routes** (`/marketing/*`)

```
POST /marketing/personas/discover
  → Discover personas from lead data

POST /marketing/creatives/generate
  → Generate AI creatives for persona

POST /marketing/budget/optimize
  → Optimize campaign budget allocation

POST /marketing/attribution/track
  → Track attribution for lead

GET /marketing/personas
  → List all personas

GET /marketing/campaigns
  → List all campaigns

GET /marketing/creatives
  → List all creatives
```

### ✅ Background Workers

**1. Persona Discovery** (`workers/marketing/discover_personas.py`)
- Schedule: Daily at 7:00 AM
- Duration: ~5-10 minutes
- Discovers new personas from recent qualifications

**2. Budget Optimization** (`workers/marketing/optimize_budgets.py`)
- Schedule: Hourly
- Duration: ~1-2 minutes
- Rebalances budgets across active campaigns

**3. Metrics Sync** (`workers/marketing/sync_metrics.py`)
- Schedule: Every 15 minutes
- Duration: ~2-5 minutes
- Syncs performance data from platforms

---

## Integration Flow

### 1. Lead Qualification → Persona Assignment

```python
# When lead qualifies via QualificationAgent
qualification = agent.qualify(lead)

# Assign to marketing persona
persona_service = PersonaDiscoveryService(db)
matched_persona = persona_service.match_lead_to_persona(lead.profile)

lead.marketing_persona_id = matched_persona.id
lead.save()
```

### 2. Persona → Campaign Creation

```python
# Generate campaign for high-value persona
creative_service = CreativeGeneratorService(db)
creatives = creative_service.generate_creatives(
    persona_id=persona.id,
    format=CreativeFormat.IMAGE,
    count=3
)

# Deploy to Meta
adapter = MetaMarketingAdapter()
campaign = await adapter.create_campaign(
    name=f"{persona.name} - Q4 2024",
    objective="LEAD_GENERATION",
    budget_daily=100.0
)
```

### 3. Attribution → Closed Loop

```python
# User clicks ad with UTM parameters
attribution_service = AttributionService(db)
attribution_data = attribution_service.parse_attribution(
    url="https://example.com?utm_campaign=123&fbclid=xyz"
)

# Lead qualifies
lead = create_lead_from_form(data)
attribution_service.attribute_lead(lead.id, attribution_data)

# Upload conversion back to platform
conversions = attribution_service.prepare_offline_conversions(
    platform="meta",
    start_date=today
)
await meta_adapter.send_conversion_event(conversions)
```

### 4. Optimization Loop

```python
# Hourly budget optimization
optimizer = BudgetOptimizerService(db)
recommendations = optimizer.optimize_campaign_budget(
    campaign_id=campaign.id,
    lookback_days=7
)

# Auto-apply if confident
if all(r.confidence > 0.8 for r in recommendations):
    optimizer.apply_recommendations(recommendations, auto_approve=True)
```

---

## Configuration

### Environment Variables

Add to `apps/api/.env`:

```bash
# Meta Marketing
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_ACCESS_TOKEN=your_access_token
META_AD_ACCOUNT_ID=act_123456789
META_PIXEL_ID=123456789012345

# Google Ads (optional)
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_CUSTOMER_ID=...

# TikTok Ads (optional)
TIKTOK_ACCESS_TOKEN=...
TIKTOK_ADVERTISER_ID=...
TIKTOK_PIXEL_ID=...

# GA4 Server Events (optional)
GA4_MEASUREMENT_ID=G-XXXXXXXXXX
GA4_API_SECRET=...
```

### Dependencies

Already added to `requirements.txt`:
- `scikit-learn==1.5.2` - Clustering algorithms
- `hdbscan==0.8.38` - Density-based clustering
- `numpy==1.26.4` - Numerical operations
- `pandas==2.2.3` - Data manipulation

---

## Database Migration

Run the marketing schema migration:

```bash
cd apps/api
alembic upgrade head
```

This creates all marketing tables and extends existing ones.

---

## Usage Examples

### Example 1: Discover Personas

```bash
curl -X POST http://localhost:8000/marketing/personas/discover \
  -H "Content-Type: application/json" \
  -d '{
    "min_cluster_size": 25,
    "method": "hdbscan"
  }'
```

Response:
```json
{
  "personas": [
    {
      "id": 1,
      "name": "Luxury Waterfront Seekers",
      "description": "High-income professionals seeking premium properties",
      "sample_size": 145,
      "confidence_score": 87.5,
      "characteristics": {
        "urgency": "high",
        "price_sensitivity": "low",
        "decision_speed": "fast"
      },
      "messaging": {
        "hooks": [
          "Exclusive waterfront living",
          "Investment opportunity",
          "Limited availability"
        ],
        "tone": "aspirational"
      }
    }
  ],
  "count": 1
}
```

### Example 2: Generate Creatives

```bash
curl -X POST http://localhost:8000/marketing/creatives/generate \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": 1,
    "format": "image",
    "count": 3
  }'
```

Response:
```json
{
  "creatives": [
    {
      "id": 1,
      "name": "Luxury Waterfront Seekers - image - Variant 1",
      "format": "image",
      "status": "approved",
      "headline": "Your Waterfront Sanctuary Awaits",
      "primary_text": "Discover exclusive properties where luxury meets the sea. Premium amenities, breathtaking views.",
      "call_to_action": "Book Private Viewing",
      "risk_flags": {
        "compliance_issues": [],
        "warnings": [],
        "toxicity_score": 0.02
      }
    }
  ],
  "count": 3
}
```

### Example 3: Optimize Budget

```bash
curl -X POST http://localhost:8000/marketing/budget/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": 1,
    "lookback_days": 7,
    "volatility_cap": 0.20,
    "auto_apply": false
  }'
```

Response:
```json
{
  "recommendations": [
    {
      "ad_set_id": 1,
      "name": "Dubai Marina - Premium",
      "current_budget": 100.0,
      "recommended_budget": 135.0,
      "change_amount": 35.0,
      "change_pct": 0.35,
      "rationale": "Increase budget due to strong performance (CVR: 8.5%, CPL: $12.50)",
      "confidence": 0.95
    },
    {
      "ad_set_id": 2,
      "name": "Downtown - Luxury",
      "current_budget": 80.0,
      "recommended_budget": 65.0,
      "change_amount": -15.0,
      "change_pct": -0.19,
      "rationale": "Decrease budget due to underperformance (CVR: 0.8%)",
      "confidence": 0.75
    }
  ],
  "count": 2,
  "applied": 0
}
```

---

## Testing

### Sandbox Mode

All adapters support dry-run mode:

```python
adapter = MetaMarketingAdapter(dry_run=True)
campaign = await adapter.create_campaign(...)  # Returns mock data
```

### Manual Worker Execution

```bash
# Discover personas
python -m app.workers.marketing.discover_personas

# Optimize budgets
python -m app.workers.marketing.optimize_budgets

# Sync metrics
python -m app.workers.marketing.sync_metrics
```

---

## Next Steps

### Phase 2: Production Deployment

1. **Platform Setup**
   - [ ] Create Meta test ad account
   - [ ] Generate access tokens
   - [ ] Set up tracking pixels
   - [ ] Configure webhooks

2. **Testing**
   - [ ] Run persona discovery on production data
   - [ ] Generate test creatives
   - [ ] Deploy campaigns in dry-run mode
   - [ ] Verify attribution tracking

3. **Celery Configuration**
   - [ ] Set up Celery beat scheduler
   - [ ] Configure job schedules
   - [ ] Set up monitoring (Flower)

4. **Frontend Integration**
   - [ ] Persona management UI
   - [ ] Campaign dashboard
   - [ ] Creative library
   - [ ] Budget optimizer interface
   - [ ] Analytics dashboards

5. **Monitoring**
   - [ ] Set up alerts for:
     - Budget overspend
     - Compliance violations
     - Poor campaign performance
     - Attribution gaps

---

## Architecture Benefits

### 1. Unified System
- Single database for leads and campaigns
- Shared authentication and logging
- Consistent API patterns

### 2. Closed-Loop Attribution
- Track every dollar spent → lead generated → deal closed
- Optimize based on actual conversions, not clicks
- Calculate true CAC and ROAS

### 3. AI-Powered Everything
- Personas discovered automatically
- Creatives generated with compliance checks
- Budgets optimized with Bayesian algorithms
- Leads qualified in real-time

### 4. Scalable Infrastructure
- Separate workers for long-running jobs
- Platform adapters easily extended
- Dry-run mode for safe testing
- Rate limiting and backoff built-in

---

## Support

For questions or issues:
1. Check logs: `docker-compose logs api`
2. Review this guide
3. Examine the code in `apps/api/app/services/marketing/`

---

**Ready to generate leads at scale! 🚀**

