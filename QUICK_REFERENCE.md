# 🚀 Quick Reference Card

**Your Real Estate Marketing Agent is READY TO USE!**

---

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Run database migration
cd apps/api
alembic upgrade head

# 2. Install dependencies (if not already done)
pip install -r requirements.txt

# 3. Start the API
uvicorn app.main:app --reload

# 4. In another terminal, start the web app
cd apps/web
npm run dev

# 5. Open browser
# - Frontend: http://localhost:5173/marketing/personas
# - API Docs: http://localhost:8000/docs
```

---

## 📍 Key URLs

### Frontend Dashboards
- **Personas**: http://localhost:5173/marketing/personas
- **Creatives**: http://localhost:5173/marketing/creatives
- **Campaigns**: http://localhost:5173/marketing/campaigns
- **Budget Optimizer**: http://localhost:5173/marketing/budget

### API Endpoints
- **Health Check**: GET http://localhost:8000/monitoring/health
- **Discover Personas**: POST http://localhost:8000/marketing/personas/discover
- **Generate Creatives**: POST http://localhost:8000/marketing/creatives/generate
- **Optimize Budget**: POST http://localhost:8000/marketing/budget/optimize
- **API Docs**: http://localhost:8000/docs

---

## 🎯 Common Tasks

### 1. Discover New Personas
```bash
curl -X POST http://localhost:8000/marketing/personas/discover \
  -H "Content-Type: application/json" \
  -d '{"min_cluster_size": 25, "method": "hdbscan"}'
```

### 2. Generate Ad Creatives
```bash
curl -X POST http://localhost:8000/marketing/creatives/generate \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": 1,
    "format": "image",
    "count": 3,
    "geo": {"city": "Dubai", "areas": ["Dubai Marina"]}
  }'
```

### 3. Optimize Campaign Budgets
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

### 4. Check System Health
```bash
curl http://localhost:8000/monitoring/health
curl http://localhost:8000/monitoring/alerts
```

---

## 🧪 Run Tests

```bash
# All marketing tests
pytest apps/api/tests/test_marketing/

# E2E test (golden path)
pytest apps/api/tests/test_e2e_marketing.py -v

# Specific test
pytest apps/api/tests/test_marketing/test_persona_discovery.py -v

# With coverage
pytest --cov=app.services.marketing apps/api/tests/test_marketing/
```

---

## 📂 Key Files

### Backend
```
apps/api/app/
├── models/              # Database models
│   ├── persona.py
│   ├── creative.py
│   └── campaign.py
├── services/marketing/  # Core business logic
│   ├── persona_discovery.py
│   ├── creative_generator.py
│   ├── budget_optimizer.py
│   └── attribution.py
├── adapters/           # Platform integrations
│   ├── meta_marketing.py
│   ├── google_ads.py
│   └── tiktok_ads.py
├── routes/             # API endpoints
│   ├── marketing.py
│   └── monitoring.py
└── monitoring.py       # Health & alerts
```

### Frontend
```
apps/web/app/marketing/
├── personas/page.tsx
├── creatives/page.tsx
├── campaigns/page.tsx
└── budget/page.tsx
```

---

## 🔧 Configuration

### Required Environment Variables
```bash
# Core
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
QDRANT_URL=http://...

# Marketing (Optional - for live campaigns)
META_ACCESS_TOKEN=...
META_AD_ACCOUNT_ID=act_...
GOOGLE_ADS_DEVELOPER_TOKEN=...
TIKTOK_ACCESS_TOKEN=...
```

See `apps/api/.env.example` for full list.

---

## 🚨 Monitoring

### Health Check Response (Healthy)
```json
{
  "status": "healthy",
  "components": {
    "database": {"status": "healthy"},
    "campaigns": {"status": "healthy", "active_count": 3},
    "leads": {"status": "healthy", "last_24h": 42}
  }
}
```

### Alert Types
- **Budget Overspend**: >110% of daily budget
- **Budget Underspend**: <50% by 6pm
- **Low CVR**: <2% conversion rate
- **High CPA**: >$500 cost per acquisition
- **Low Attribution**: <50% of leads attributed

---

## 🎨 Frontend Components

### Persona Card
- Name, description, sample size
- Budget range
- Characteristics (urgency, price sensitivity)
- Messaging hooks
- Actions: Generate creatives, View campaigns

### Creative Card
- Headline, primary text, description
- Call to action
- Compliance status (approved/review)
- Risk flags
- Actions: Edit, Use in campaign

### Budget Optimizer
- Current vs recommended budget
- Change percentage
- Confidence score
- Rationale
- Action: Apply changes

---

## 📊 Metrics & KPIs

### Marketing Performance
- **CAC**: Cost per Acquisition
- **ROAS**: Return on Ad Spend
- **CVR**: Conversion Rate (leads → closed)
- **CPC**: Cost per Click
- **CPL**: Cost per Lead
- **Attribution Rate**: % of leads with attribution data

### System Health
- API uptime
- Error rate
- Response time p95
- Active campaigns
- Recent leads

---

## 🛠️ Troubleshooting

### "No personas discovered"
- Need at least 25 qualified leads
- Check that leads have profiles (budget, location, etc.)
- Try lowering `min_cluster_size`

### "Creative generation failed"
- Check `OPENAI_API_KEY` is set
- Verify persona exists: `GET /marketing/personas`
- Check API logs for details

### "Budget optimizer returns no recommendations"
- Need at least 7 days of campaign data
- Check that campaigns have metrics
- Verify ad sets are active

### "Low attribution rate"
- Check UTM parameters are being captured
- Verify tracking pixels installed
- Review webhook configuration

---

## 📚 Documentation

- **Full Guide**: `MARKETING_INTEGRATION_GUIDE.md`
- **Quick Start**: `MARKETING_QUICKSTART.md`
- **Summary**: `MARKETING_AGENT_SUMMARY.md`
- **Deployment**: `DEPLOYMENT_GUIDE.md`
- **Complete Status**: `COMPLETE_IMPLEMENTATION_SUMMARY.md`

---

## 💡 Pro Tips

1. **Start Small**: Use dry-run mode for campaigns initially
2. **Monitor Closely**: Check `/monitoring/alerts` daily
3. **Test Locally**: Run E2E test before deploying
4. **Budget Safely**: Set low daily limits initially
5. **Track Attribution**: Always use UTM parameters

---

## 🎯 Workflow Summary

```
1. Leads accumulate → Personas discovered automatically (daily)
   ↓
2. Select persona → Generate creatives (with compliance)
   ↓
3. Review creatives → Deploy campaign (dry-run first)
   ↓
4. Campaign runs → Metrics collected (every 15 min)
   ↓
5. Budget optimized → Thompson Sampling (hourly)
   ↓
6. Leads attributed → Close loop (Meta CAPI)
   ↓
7. Monitor health → Alerts if issues
```

---

## 🚀 You're Ready!

**Everything is built and tested.**  
**Time to generate leads at scale!**

Questions? Check the docs or review the test files for examples.

---

**Validation Status**: ✅ ALL CHECKS PASSED

Run `python scripts/validate_marketing_setup.py` anytime to verify.

