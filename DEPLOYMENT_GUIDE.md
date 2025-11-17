# Production Deployment Guide

Complete guide for deploying the marketing-integrated CRM to production.

## Pre-Deployment Checklist

### 1. Database Migration ✅
```bash
cd apps/api
alembic upgrade head
```

### 2. Environment Variables

**Required:**
- `OPENAI_API_KEY` - For AI agents
- `DATABASE_URL` - Production PostgreSQL
- `REDIS_URL` - Production Redis
- `QDRANT_URL` - Vector database

**Optional (Marketing):**
- `META_ACCESS_TOKEN` - For Meta campaigns
- `META_AD_ACCOUNT_ID` - Meta ad account
- `GOOGLE_ADS_*` - For Google Ads
- `TIKTOK_*` - For TikTok Ads

### 3. Dependencies
```bash
pip install -r apps/api/requirements.txt
npm install --prefix apps/web
```

---

## Deployment Options

### Option 1: Render (Recommended - Easiest)

**Step 1: Push to GitHub**
```bash
git add .
git commit -m "Add marketing agent"
git push origin main
```

**Step 2: Connect to Render**
1. Go to https://render.com
2. Connect your GitHub repository
3. Render will auto-detect `render.yaml`

**Step 3: Add Secrets**
In Render dashboard, add environment variables:
- `OPENAI_API_KEY`
- `META_ACCESS_TOKEN` (optional)

**Step 4: Deploy**
- Render will automatically deploy all services
- Monitor deployment logs
- Access health check: `https://your-app.onrender.com/health`

**Services Created:**
- API (FastAPI)
- Web (Next.js)
- Worker (Celery - optional)
- PostgreSQL
- Redis
- Qdrant

---

### Option 2: Docker Compose (Manual Server)

**Step 1: Build Images**
```bash
# Build all services
docker-compose -f infra/docker-compose.dev.yml build
```

**Step 2: Set Environment**
```bash
# Create production .env
cp apps/api/.env.example apps/api/.env
# Edit and add production values
```

**Step 3: Deploy**
```bash
# Start all services
docker-compose -f infra/docker-compose.dev.yml up -d

# Check health
curl http://localhost:8000/health
```

**Step 4: Run Migrations**
```bash
docker-compose exec api alembic upgrade head
```

---

### Option 3: Kubernetes (Advanced)

See `infra/k8s/` for Kubernetes manifests (to be created).

---

## Post-Deployment Steps

### 1. Verify Health
```bash
curl https://your-api.com/health
curl https://your-api.com/monitoring/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "database": {"status": "healthy"},
    "campaigns": {"status": "healthy", "active_count": 0},
    "leads": {"status": "healthy", "last_24h": 0}
  }
}
```

### 2. Test Endpoints
```bash
# Test persona discovery
curl -X POST https://your-api.com/marketing/personas/discover \
  -H "Content-Type: application/json" \
  -d '{"min_cluster_size": 25, "method": "hdbscan"}'

# Test creative generation (requires persona)
curl -X POST https://your-api.com/marketing/creatives/generate \
  -H "Content-Type: application/json" \
  -d '{"persona_id": 1, "format": "image", "count": 3}'
```

### 3. Set Up Monitoring

**Option A: Built-in Monitoring**
```bash
# Check for alerts
curl https://your-api.com/monitoring/alerts

# Full monitoring check
curl https://your-api.com/monitoring/monitoring
```

**Option B: External Monitoring (Recommended)**

Set up external monitoring with:
- **Sentry** - Error tracking
- **Datadog/New Relic** - Performance monitoring
- **PagerDuty** - Alert notifications

Install Sentry:
```bash
pip install sentry-sdk
```

Add to `apps/api/app/main.py`:
```python
import sentry_sdk

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    traces_sample_rate=0.1,
    environment=settings.environment
)
```

### 4. Configure Celery Workers (Optional)

For automated persona discovery and budget optimization:

```bash
# Start Celery worker
celery -A app.workers.celery_app worker -l INFO

# Start Celery beat (scheduler)
celery -A app.workers.celery_app beat -l INFO
```

**Scheduled Jobs:**
- Persona discovery: Daily at 7:00 AM
- Budget optimization: Hourly
- Metrics sync: Every 15 minutes

---

## Gradual Rollout Strategy

### Phase 1: Staging (Week 1)

**Goals:**
- Deploy to staging environment
- Test with synthetic data
- Verify all endpoints work
- Run E2E tests

**Steps:**
1. Deploy to staging URL
2. Run test suite: `pytest apps/api/tests/`
3. Manually test all marketing endpoints
4. Generate test personas and creatives
5. Monitor for 7 days

**Success Criteria:**
- All health checks pass
- No errors in logs
- API response times < 500ms p95
- All tests passing

### Phase 2: Soft Launch (Week 2)

**Goals:**
- Deploy to production
- Enable for 10% of traffic
- Monitor closely

**Steps:**
1. Deploy to production
2. Create 1-2 test campaigns in **dry-run mode**
3. Attribute test leads
4. Monitor dashboards

**Budget Limits:**
- Start with $10/day total budget
- Max $5 per ad set
- Manual approval required for changes

**Monitoring:**
- Check alerts every 4 hours
- Review logs daily
- Track attribution rate

### Phase 3: Scale Up (Week 3-4)

**If Phase 2 successful:**
- Increase budget to $50/day
- Enable auto-optimization (with constraints)
- Add more personas

**Steps:**
1. Review Phase 2 metrics
2. Increase budget limits
3. Enable automatic budget optimization
4. Scale to more campaigns

### Phase 4: Full Production (Month 2)

**Full rollout:**
- Remove budget constraints
- Enable all platforms
- Full automation

---

## Budget Safety Constraints

### Hard Limits (Cannot Exceed)

```python
# In app/config.py
BUDGET_HARD_LIMITS = {
    "daily_max_per_campaign": 500.0,  # $500/day max
    "daily_max_total": 2000.0,        # $2000/day across all
    "monthly_max_total": 40000.0,     # $40k/month total
}
```

### Soft Limits (Alert Only)

```python
BUDGET_ALERT_THRESHOLDS = {
    "daily_spend_rate": 0.9,   # Alert at 90% of daily budget
    "overspend_tolerance": 1.1, # Alert at 110% overspend
}
```

### Automatic Pausing

Campaigns automatically pause if:
- Spend exceeds 120% of daily budget
- CPA > $500 for 3 consecutive days
- CVR < 1% with > 100 leads
- Attribution rate < 20%

---

## Monitoring Dashboard URLs

Once deployed, monitor at:
- **Health**: `https://your-api.com/monitoring/health`
- **Alerts**: `https://your-api.com/monitoring/alerts`
- **Full Check**: `https://your-api.com/monitoring/monitoring`
- **API Docs**: `https://your-api.com/docs`

---

## Rollback Procedure

If issues arise:

### Quick Rollback
```bash
# Render: Use dashboard to rollback to previous deploy
# Docker: 
docker-compose down
git checkout <previous-commit>
docker-compose up -d
```

### Database Rollback
```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>
```

### Emergency Pause
```bash
# Pause all campaigns via API
curl -X POST https://your-api.com/marketing/campaigns/pause-all

# Or directly in database
UPDATE campaigns SET status = 'paused' WHERE status = 'active';
```

---

## Performance Targets

### API Response Times
- p50: < 200ms
- p95: < 500ms
- p99: < 1000ms

### Background Jobs
- Persona discovery: < 10 minutes
- Budget optimization: < 2 minutes
- Metrics sync: < 5 minutes

### System Health
- Uptime: > 99.5%
- Error rate: < 0.1%
- Alert response time: < 15 minutes

---

## Cost Estimates

### Infrastructure (Render - Starter Plan)
- API: $7/month
- Web: $7/month
- PostgreSQL: $7/month
- Redis: $10/month
- Qdrant: $10/month
**Total: ~$41/month**

### API Costs
- OpenAI (GPT-4): ~$0.01-0.05 per lead qualification
- OpenAI (Embeddings): ~$0.0001 per lead
- Persona discovery: ~$0.50 per run (daily)
- Creative generation: ~$0.05 per creative

**Estimated: $50-200/month** (depends on volume)

### Advertising Spend
- Your budget (flexible)
- Start: $300/month ($10/day)
- Scale: $3000-15000/month

---

## Support & Troubleshooting

### Common Issues

**1. High CPA**
- Review creative compliance
- Check targeting accuracy
- Analyze persona fit
- Compare with benchmarks

**2. Low Attribution Rate**
- Verify tracking pixels installed
- Check UTM parameters
- Review webhook configuration
- Test click tracking

**3. Budget Overspend**
- Check automatic pause rules
- Review optimization frequency
- Verify platform sync
- Check for duplicate campaigns

### Getting Help

1. Check logs: `docker-compose logs api`
2. Review monitoring: `/monitoring/alerts`
3. Run health check: `/monitoring/health`
4. Check documentation in repo

---

## Success Metrics

Track these KPIs weekly:

### Marketing Performance
- CAC (Cost per Acquisition)
- ROAS (Return on Ad Spend)
- CVR (Conversion Rate)
- Attribution Rate

### System Performance
- API uptime
- Error rate
- Response time p95
- Alert resolution time

### Business Impact
- Leads generated
- Qualified leads %
- Deals closed
- Revenue attributed

---

**Deployment Complete!** 🚀

Monitor closely for first 2 weeks, then scale confidently.

