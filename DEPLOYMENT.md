# Deployment Guide

Complete guide for deploying the Real Estate AI CRM to production.

## Pre-Deployment Checklist

- [ ] OpenAI API key with sufficient credits
- [ ] GitHub repository created
- [ ] Render account created
- [ ] Environment variables documented
- [ ] Database backups configured
- [ ] Error monitoring setup (optional)

## Deployment Options

### Option 1: Render (Recommended)

Render provides managed services and auto-deployment from GitHub.

#### Step 1: Prepare Repository

```bash
# Initialize git if not already
git init
git add .
git commit -m "Initial commit"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

#### Step 2: Create Render Account

1. Sign up at [render.com](https://render.com)
2. Connect your GitHub account

#### Step 3: Deploy via Blueprint

1. In Render Dashboard, click "New" → "Blueprint"
2. Select your repository
3. Render will detect `render.yaml`
4. Click "Apply"

#### Step 4: Set Environment Variables

In Render Dashboard, for each service:

**realestate-api**:
- `OPENAI_API_KEY`: Your OpenAI key (required)
- `APP_SECRET`: Random string for webhook security (optional)
- `LOG_LEVEL`: `INFO` or `DEBUG`

**realestate-web**:
- Auto-configured via blueprint

#### Step 5: Run Migrations

After first deploy:

```bash
# SSH into API service or use Render Shell
render ssh realestate-api

# Inside container
alembic upgrade head
python -m app.workers.seed_data
python -m app.workers.embed_units
```

#### Step 6: Verify Deployment

```bash
# Check API health
curl https://realestate-api.onrender.com/health

# Check Web
curl https://realestate-web.onrender.com
```

### Option 2: Docker + VPS

Deploy to any VPS (DigitalOcean, Linode, etc.) using Docker Compose.

#### Step 1: Provision VPS

```bash
# Minimum specs:
# - 2 vCPUs
# - 4GB RAM
# - 50GB SSD

# SSH into server
ssh root@YOUR_SERVER_IP
```

#### Step 2: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get update
apt-get install docker-compose-plugin
```

#### Step 3: Clone Repository

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git quali
cd quali
```

#### Step 4: Configure Environment

```bash
# API
cp apps/api/.env.example apps/api/.env
nano apps/api/.env  # Add OPENAI_API_KEY

# Web
cp apps/web/.env.example apps/web/.env
nano apps/web/.env  # Set NEXT_PUBLIC_API_BASE to your domain
```

#### Step 5: Start Services

```bash
cd infra
docker-compose -f docker-compose.dev.yml up -d

# Check logs
docker-compose -f docker-compose.dev.yml logs -f
```

#### Step 6: Setup Nginx Reverse Proxy

```bash
apt-get install nginx

# Create nginx config
cat > /etc/nginx/sites-available/quali <<EOF
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/quali /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### Step 7: Setup SSL with Let's Encrypt

```bash
apt-get install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

### Option 3: Kubernetes (Advanced)

For high-scale deployments.

```yaml
# k8s/deployment.yaml (example)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: realestate-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: YOUR_REGISTRY/realestate-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-key
```

## Environment Variables Reference

### Backend (API)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `REDIS_URL` | Yes | - | Redis connection string |
| `QDRANT_URL` | Yes | - | Qdrant server URL |
| `QDRANT_API_KEY` | No | - | Qdrant API key (if auth enabled) |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `APP_SECRET` | No | - | Secret for webhook validation |
| `ENVIRONMENT` | No | `development` | `development` or `production` |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Frontend (Web)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE` | Yes | - | Backend API base URL |

## Database Management

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "add_new_field"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current
```

### Backups

#### PostgreSQL Backups

```bash
# Manual backup
pg_dump $DATABASE_URL > backup-$(date +%F).sql

# Restore
psql $DATABASE_URL < backup-2024-10-22.sql

# Automated daily backups (cron)
0 2 * * * pg_dump $DATABASE_URL | gzip > /backups/backup-$(date +\%F).sql.gz
```

#### Qdrant Backups

```bash
# Backup Qdrant data
docker exec qdrant tar -czf /tmp/qdrant-backup.tar.gz /qdrant/storage
docker cp qdrant:/tmp/qdrant-backup.tar.gz ./qdrant-backup-$(date +%F).tar.gz

# Restore
docker cp qdrant-backup-2024-10-22.tar.gz qdrant:/tmp/
docker exec qdrant tar -xzf /tmp/qdrant-backup-2024-10-22.tar.gz -C /
docker restart qdrant
```

## Monitoring

### Health Checks

```bash
# API health
curl https://api.yourdomain.com/health

# Check specific services
curl https://api.yourdomain.com/health | jq
```

### Logs

#### Render

- View logs in Render Dashboard
- Download logs: `render logs SERVICE_NAME`

#### Docker

```bash
# View logs
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Search logs
docker-compose logs api | grep ERROR
```

### Metrics (Optional)

Add Prometheus + Grafana:

```bash
# Add to docker-compose
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:5173"
```

## Security

### API Security Checklist

- [ ] Enable `APP_SECRET` for webhook validation
- [ ] Use HTTPS/TLS for all endpoints
- [ ] Rotate OpenAI API key regularly
- [ ] Enable rate limiting (future)
- [ ] Set up CORS whitelist
- [ ] Validate webhook signatures (Meta)

### Database Security

- [ ] Use strong passwords
- [ ] Enable SSL for database connections
- [ ] Restrict database access by IP
- [ ] Regular backups
- [ ] Encrypt sensitive fields (future)

### Container Security

- [ ] Use non-root users in containers
- [ ] Scan images for vulnerabilities
- [ ] Keep base images updated
- [ ] Use secrets management

## Scaling

### Vertical Scaling

Increase resources per service:

**Render**: Upgrade plan in dashboard
**Docker**: Update resource limits in docker-compose

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Horizontal Scaling

Add more instances:

**API**: Stateless, scale freely
- Render: Adjust instance count in dashboard
- K8s: `kubectl scale deployment api --replicas=5`

**Workers**: Add background job consumers
- Use RQ or Celery for async tasks

**Database**: 
- Add read replicas for reports
- Use connection pooling (PgBouncer)

**Qdrant**:
- Cluster mode for high availability
- Shard collections by lead volume

## Troubleshooting

### Common Issues

#### 1. Migration Failures

```bash
# Check current version
alembic current

# Check pending migrations
alembic heads

# Manual fix
alembic stamp head
alembic upgrade head
```

#### 2. Qdrant Connection Failed

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Check logs
docker logs qdrant

# Restart
docker restart qdrant
```

#### 3. OpenAI Rate Limits

```bash
# Check usage
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Implement rate limiting in code
# Add backoff/retry logic
```

#### 4. Database Connection Pool Exhausted

```bash
# Increase pool size in config.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
)
```

### Debugging

#### Enable Debug Logs

```bash
# In .env
LOG_LEVEL=DEBUG

# View structured logs
docker-compose logs api | jq
```

#### Database Queries

```bash
# Connect to database
docker exec -it postgres psql -U dev -d app

# Check lead count
SELECT COUNT(*) FROM leads;

# Recent qualifications
SELECT * FROM qualifications ORDER BY created_at DESC LIMIT 10;
```

## Cost Estimation

### Render (Starter)

- **API**: $7/month (Starter)
- **Web**: $7/month (Starter)
- **PostgreSQL**: $7/month (Starter, 256MB)
- **Redis**: $10/month (Starter, 256MB)
- **Qdrant**: $7/month (Private service + disk)
- **Total**: ~$38/month

### OpenAI API

- **GPT-4o-mini**: $0.15/1M input tokens, $0.60/1M output tokens
- **Embeddings**: $0.02/1M tokens
- **Estimate**: $50-200/month depending on volume

### Total Monthly Cost

- **Infra**: $38
- **AI**: $50-200
- **Total**: ~$90-240/month

## Maintenance

### Weekly

- [ ] Review logs for errors
- [ ] Check API response times
- [ ] Monitor OpenAI usage/costs

### Monthly

- [ ] Database backups verification
- [ ] Update dependencies
- [ ] Review qualification scores
- [ ] Run evals (when implemented)

### Quarterly

- [ ] Tune scoring weights
- [ ] Update prompts
- [ ] Security audit
- [ ] Performance optimization

## Rollback Plan

### Render

1. Go to deployment history
2. Click "Rollback" on previous deploy
3. Wait 2-3 minutes for redeployment

### Docker

```bash
# Pull previous image
docker pull YOUR_REGISTRY/api:PREVIOUS_TAG

# Update docker-compose
docker-compose up -d --force-recreate api

# Rollback migrations if needed
alembic downgrade -1
```

## Support & Resources

- **API Docs**: https://api.yourdomain.com/docs
- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Next.js Docs**: https://nextjs.org/docs
- **Qdrant Docs**: https://qdrant.tech/documentation

## Post-Deployment

1. **Test all endpoints**
   ```bash
   # Health check
   curl https://api.yourdomain.com/health
   
   # Create test lead
   curl -X POST https://api.yourdomain.com/webhooks/leadads ...
   ```

2. **Monitor for 24 hours**
   - Check error rates
   - Monitor response times
   - Watch resource usage

3. **Configure webhooks**
   - Meta Lead Ads: Set webhook URL to `https://api.yourdomain.com/webhooks/leadads`
   - WhatsApp: Set webhook URL to `https://api.yourdomain.com/webhooks/whatsapp`

4. **Enable monitoring** (optional)
   - Sentry for error tracking
   - LogRocket for session replay
   - Datadog/New Relic for APM

Congratulations on deploying! 🎉
