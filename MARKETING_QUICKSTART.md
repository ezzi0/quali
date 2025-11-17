# Marketing Agent Quick Start

Get the marketing agent running in 10 minutes.

## 1. Run Database Migration

```bash
cd apps/api
alembic upgrade head
```

This creates all marketing tables.

## 2. Install New Dependencies

```bash
cd apps/api
pip install -r requirements.txt
```

New packages: scikit-learn, hdbscan, numpy, pandas

## 3. Update Environment Variables

Add to `apps/api/.env`:

```bash
# Meta (optional - works in dry-run mode without)
META_ACCESS_TOKEN=your_token_here
META_AD_ACCOUNT_ID=act_123456789
META_PIXEL_ID=123456789012345
```

## 4. Start the API

```bash
# From project root
make api

# Or manually
cd apps/api
uvicorn app.main:app --reload --port 8000
```

## 5. Test Persona Discovery

```bash
curl -X POST http://localhost:8000/marketing/personas/discover \
  -H "Content-Type: application/json" \
  -d '{
    "min_cluster_size": 25,
    "method": "hdbscan"
  }'
```

Expected response:
```json
{
  "personas": [
    {
      "id": 1,
      "name": "High-Value Buyers",
      "description": "Affluent buyers seeking premium properties",
      "sample_size": 145,
      "confidence_score": 87.5
    }
  ],
  "count": 1
}
```

## 6. Generate Creatives

```bash
curl -X POST http://localhost:8000/marketing/creatives/generate \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": 1,
    "format": "image",
    "count": 3
  }'
```

## 7. List All Personas

```bash
curl http://localhost:8000/marketing/personas
```

## 8. View API Documentation

Open browser to: http://localhost:8000/docs

Explore all marketing endpoints interactively.

## Common Commands

### Run Workers Manually

```bash
# Discover personas
python -m app.workers.marketing.discover_personas

# Optimize budgets
python -m app.workers.marketing.optimize_budgets

# Sync metrics
python -m app.workers.marketing.sync_metrics
```

### Check Database

```bash
# Connect to postgres
psql postgresql://dev:dev@localhost:5432/app

# List marketing tables
\dt personas
\dt campaigns
\dt creatives

# Count personas
SELECT COUNT(*) FROM personas;
```

## Troubleshooting

### "No leads found for clustering"
- Need at least 50 qualified leads
- Run seed data: `python -m app.workers.seed_data`
- Or create leads via API

### "OpenAI API key not set"
- Add to `.env`: `OPENAI_API_KEY=sk-proj-...`
- Restart API

### "Import error: hdbscan"
- Run: `pip install -r requirements.txt`
- May need system dependencies on some platforms

### "No module named 'sklearn'"
- Package is `scikit-learn` not `sklearn`
- Run: `pip install scikit-learn==1.5.2`

## Next Steps

1. **Add More Leads**: Import real lead data or use qualification agent
2. **Configure Meta**: Set up test ad account and tokens
3. **Build Frontend**: Create marketing dashboard UI
4. **Set Up Workers**: Configure Celery beat for automation
5. **Deploy**: Follow deployment guide

## Documentation

- Full guide: `MARKETING_INTEGRATION_GUIDE.md`
- Summary: `MARKETING_AGENT_SUMMARY.md`
- Architecture: `ARCHITECTURE.md`
- API docs: http://localhost:8000/docs

---

**Ready to generate leads at scale!** 🚀

