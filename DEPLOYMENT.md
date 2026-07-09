# CLARIQ Deployment Guide

This guide covers production deployment to various cloud platforms.

## Prerequisites

- Docker & Docker Compose installed
- Git repository access
- Domain name (tryclariq.com) configured with DNS
- SSL certificates (Let's Encrypt recommended)
- Cloud account (AWS/Railway/DigitalOcean/etc)

---

## 🌐 Domain Setup (CRITICAL FIRST STEP)

**BEFORE deploying, configure your domain!**

See [DNS_SETUP.md](DNS_SETUP.md) for complete instructions:

1. **Update DNS records** to point to your infrastructure
2. **Setup SSL/TLS certificate** (automated via Let's Encrypt)
3. **Verify domain resolution** before deployment
4. **Update .env.production** with correct domain URLs

```bash
# Expected DNS records after setup:
# tryclariq.com      A      your.public.ip
# www.tryclariq.com  CNAME  tryclariq.com
# api.tryclariq.com  CNAME  tryclariq.com
```

---

## Option 1: Docker Compose (Self-Hosted)

### Local Setup

```bash
# Clone repository
git clone https://github.com/Epunav1/clariq.git
cd clariq

# Create environment files
cp .env.production.example .env.production
# Edit .env.production with your credentials

# Generate SSL certificates (self-signed for dev)
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes

# Build and start
docker-compose up -d
```

### Verify Deployment

```bash
# Check service health
docker-compose ps
docker-compose logs -f backend

# Test API (locally)
curl https://localhost/api/health

# Access dashboard (from configured domain)
open https://tryclariq.com

# Verify API endpoint
curl https://api.tryclariq.com/api/health
```

---

## Option 2: Railway.app (Recommended)

### Setup

1. Connect GitHub repository to Railway
2. Add environment variables from `.env.production`
3. Configure build:
   ```bash
   Framework: Docker
   Dockerfile: ./Dockerfile
   ```

4. Add services:
   - Backend (Docker)
   - PostgreSQL (Railway template)
   - Redis (optional, for caching)

5. Configure domain:
   - Railway → Project → Domains
   - Add custom domain
   - Enable SSL (auto)

### Deploy

```bash
# Via Railway CLI
railway up

# Or push to main branch for auto-deploy
git push origin main
```

---

## Option 3: AWS Deployment

### Using ECS + ALB

1. **Create RDS Instance**
   ```bash
   Engine: PostgreSQL 15
   Instance class: db.t3.micro
   Storage: 20GB
   ```

2. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name clariq-backend
   ```

3. **Build & Push Image**
   ```bash
   docker build -t clariq-backend .
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   docker tag clariq-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/clariq-backend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/clariq-backend:latest
   ```

4. **Create ECS Task Definition**
   - Container: clariq-backend ECR image
   - Port: 8000
   - Memory: 512MB, CPU: 256
   - Environment variables from Secrets Manager

5. **Create ECS Service**
   - Launch type: Fargate
   - Desired count: 2 (for high availability)
   - Load balancer: Application Load Balancer
   - Target group: /api/health

6. **Configure ALB**
   - HTTPS listener with ACM certificate
   - Target group: port 8000
   - Health check path: /api/health

---

## Option 4: DigitalOcean App Platform

1. Connect GitHub repository
2. Configure:
   ```yaml
   Name: clariq-backend
   Environment: Docker
   Build command: docker build -t clariq-backend .
   Run command: gunicorn --bind 0.0.0.0:8000 main:app
   ```

3. Set environment variables
4. Configure HTTP routes: /api/*
5. Add database: PostgreSQL
6. Deploy with auto-SSL

---

## Security Hardening

### 1. SSL/TLS Configuration

```bash
# Generate Let's Encrypt certificate
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d clariq.com -d www.clariq.com

# Update nginx.conf with certificate paths
```

### 2. Database Security

```bash
# PostgreSQL
ALTER ROLE clariq WITH PASSWORD 'strong-password';
REVOKE ALL ON DATABASE clariq FROM public;
GRANT CONNECT ON DATABASE clariq TO clariq;
GRANT USAGE ON SCHEMA public TO clariq;

# SQLite (file permissions)
chmod 600 data/clariq.db
chmod 700 data/
```

### 3. API Security

```python
# Enable rate limiting (already in nginx.conf)
# Add API key authentication for external integrations
# Implement CORS properly for your domain
# Use environment variables for all secrets
```

### 4. Network Security

```bash
# Firewall rules (if self-hosted)
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
```

---

## Database Backup & Migration

### Automated Backups

```bash
# Create backup script: backup.sh
#!/bin/bash
BACKUP_DIR="./data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# SQLite backup
cp ./data/clariq.db $BACKUP_DIR/clariq_$TIMESTAMP.db

# PostgreSQL backup (if used)
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB > \
  $BACKUP_DIR/postgres_$TIMESTAMP.sql

# Keep only last 30 days
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/clariq_$TIMESTAMP.db"
```

### Cron Schedule

```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/clariq && bash backup.sh
```

---

## Monitoring & Logging

### Application Monitoring

```python
# Check /api/performance/health for:
# - API response times
# - Error rates
# - System resources
# - Database connectivity
# - Sync status
```

### Centralized Logging

```bash
# Option 1: Sentry
SENTRY_DSN=https://key@sentry.io/project

# Option 2: CloudWatch (AWS)
pip install watchtower

# Option 3: ELK Stack
docker-compose add elasticsearch logstash kibana
```

### Alerts Setup

```bash
# Email alerts for:
# - High error rate (>5%)
# - High response time (>1s p95)
# - Database errors
# - Sync failures
# - Low disk space
```

---

## Scaling Strategy

### Horizontal Scaling

```yaml
# docker-compose.yml - Multiple backend instances
services:
  backend:
    deploy:
      replicas: 3  # Scale to 3 instances
```

### Load Balancing (nginx)

```nginx
upstream clariq_backend {
    least_conn;
    server backend:8000;
    server backend_2:8000;
    server backend_3:8000;
}
```

### Database Connection Pooling

```python
# In main.py, add connection pool for PostgreSQL
from databases import Database
DATABASE_URL = "postgresql://user:pass@postgres/clariq"
database = Database(DATABASE_URL)
```

---

## Rollback Procedure

```bash
# If deployment fails, rollback to previous version
docker-compose pull
git checkout previous-stable-tag
docker-compose up -d --force-recreate

# Verify health
curl https://clariq.com/api/health
```

---

## Performance Optimization

### Caching Layer (Redis)

```bash
# Add to docker-compose.yml
redis:
  image: redis:latest
  ports:
    - "6379:6379"
```

### Database Indexing

```sql
-- Ensure production indexes
CREATE INDEX idx_pilots_status ON pilots(status);
CREATE INDEX idx_actions_pilot ON actions(pilot_id);
CREATE INDEX idx_alerts_sent ON alerts(sent);
```

### CDN Setup

```nginx
# Serve static assets via CloudFlare CDN
# Cache-Control headers configured in nginx.conf
```

---

## Troubleshooting

### Backend won't start

```bash
docker-compose logs backend
# Check: PORT conflict, database connection, missing env vars
```

### High memory usage

```bash
docker stats
# Consider: increasing gunicorn workers, reducing buffer sizes
```

### Slow API responses

```bash
# Check /api/performance/api-metrics
# Look for: database query time, missing indices
```

---

## Next Steps

1. ✅ Configure .env.production
2. ✅ Setup SSL certificates
3. ✅ Choose deployment platform
4. ✅ Deploy and test
5. ✅ Setup monitoring
6. ✅ Configure backups
7. ✅ Performance testing
