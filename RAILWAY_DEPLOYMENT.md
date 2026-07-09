# Railway Production Deployment Guide

Deploy CLARIQ to production in under 10 minutes using Railway.app.

---

## 🚀 Why Railway?

✅ **Easiest Setup**: 1-click GitHub integration  
✅ **Auto-Deploy**: Push to GitHub → Automatic deployment  
✅ **Free Tier**: Start for free, $5-50/month production  
✅ **SSL/TLS**: Automatic HTTPS certificates  
✅ **Database**: PostgreSQL, Redis included  
✅ **Environment Variables**: Easy management  
✅ **Monitoring**: Built-in logs and metrics  

---

## 📋 Prerequisites

- GitHub account with clariq repository
- Railway.app account (free at railway.app)
- tryclariq.com domain (for DNS setup)

---

## 🎯 Step 1: Connect GitHub Repository

### 1.1 Create Railway Account

```bash
# Go to https://railway.app
# Sign up with GitHub account
# Authorize Railway to access your repositories
```

### 1.2 Create New Project

```
1. Click "Create a new project"
2. Select "Deploy from GitHub repo"
3. Search for: clariq
4. Select: Epunav1/clariq
5. Click "Deploy Now"
```

---

## 🔧 Step 2: Configure Environment Variables

### 2.1 Add Environment Variables

In Railway Dashboard:

```
1. Go to Variables tab
2. Add each variable from .env.production.example
3. Key variables:

Application:
  ENVIRONMENT=production
  DEBUG=false
  
Domain:
  BACKEND_URL=https://api.tryclariq.com
  FRONTEND_URL=https://tryclariq.com
  CORS_ORIGINS=https://tryclariq.com,https://www.tryclariq.com,https://api.tryclariq.com

Database:
  DATABASE_URL=sqlite:///./data/clariq.db
  (Railway will auto-manage PostgreSQL if needed)

Integrations (add your keys):
  STRIPE_SECRET_KEY=sk_test_...
  STRIPE_PUBLISHABLE_KEY=pk_test_...
  SLACK_BOT_TOKEN=xoxb-...
  SLACK_WEBHOOK_URL=https://hooks.slack.com/...
  GOOGLE_SHEETS_CREDENTIALS={...json...}
  GOOGLE_SHEETS_SPREADSHEET_ID=...
```

### 2.2 Critical Environment Variables

```bash
# These MUST be set for production
ENVIRONMENT=production
DEBUG=false
BACKEND_URL=https://api.tryclariq.com
FRONTEND_URL=https://tryclariq.com

# Generate a random secret for JWT
JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
# Add this JWT_SECRET to Railway variables
```

---

## 📦 Step 3: Configure Docker Build

### 3.1 Railway Auto-Detects Dockerfile

Railway automatically uses your `Dockerfile` for building:

```dockerfile
# In Dockerfile (already configured)
FROM python:3.11-slim as builder
COPY backend/requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
WORKDIR /app
COPY backend .
ENV PATH=/root/.local/bin:$PATH
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
```

### 3.2 Verify Build Settings

```
In Railway Dashboard:
1. Settings → Deployment
2. Buildpack: Dockerfile (auto-detected)
3. Watch for "Build" step to pass
```

---

## 🌐 Step 4: Configure Domain

### 4.1 Get Railway Public URL

```
1. In Railway Dashboard → Project
2. Find "Deployments" tab
3. Copy the public URL (something.railway.app)
```

### 4.2 Update DNS Records

At your domain registrar (GoDaddy, Namecheap, Route53, etc):

```
# Main domain
Type:  CNAME
Name:  tryclariq.com (or @)
Value: yourproject.railway.app
TTL:   300

# WWW redirect
Type:  CNAME
Name:  www
Value: tryclariq.com
TTL:   300

# API subdomain
Type:  CNAME
Name:  api
Value: tryclariq.com
TTL:   300
```

### 4.3 Railway Custom Domain

```
In Railway Dashboard:
1. Deployments → Settings
2. Add Custom Domain
3. Enter: tryclariq.com
4. Railway auto-provisions SSL certificate
5. Wait 5-10 minutes for DNS propagation
```

---

## ✅ Step 5: Verify Deployment

### 5.1 Test Endpoints

```bash
# Health check
curl https://tryclariq.com/api/health

# Should return:
# {"status": "ok"}

# API test
curl https://api.tryclariq.com/api/pilot

# Dashboard
open https://tryclariq.com
```

### 5.2 Check Logs

```
In Railway Dashboard:
1. Go to Deployments tab
2. Click current deployment
3. View logs for errors
4. Metrics tab shows response times
```

### 5.3 Monitor Performance

```
Railway Dashboard:
- Deployments: Shows build/deploy status
- Metrics: CPU, memory, response times
- Logs: Real-time application logs
- Environment: View all variables
```

---

## 🔄 Step 6: Setup Auto-Deploy

### 6.1 GitHub Integration (Auto)

```
Railway auto-deploys when you:
1. Push to main branch
2. PR merged to main
3. Tag release on GitHub

Workflow:
  Code Push → GitHub → Railway Auto-Build → Deploy
  (Takes 5-10 minutes)
```

### 6.2 Manual Deploy

```
If needed in Railway Dashboard:
1. Go to Deployments
2. Click "Redeploy" button
3. Wait for build to complete
```

---

## 💻 Step 7: Setup Database (Optional)

### 7.1 Use PostgreSQL in Production

For better performance, use Railway's PostgreSQL:

```bash
# In Railway Dashboard:
1. Click "Add Service"
2. Select PostgreSQL
3. Auto-generates DATABASE_URL variable
4. Replace SQLite DATABASE_URL with PostgreSQL one
5. Redeploy
```

### 7.2 Database Backups

```bash
# Railway auto-handles backups
# In Dashboard → Plugins
# Enable: PostgreSQL Backups

# Daily automatic backups included in Professional plan
```

---

## 🔐 Step 8: SSL/TLS Configuration

### 8.1 Railway Auto-SSL

```
Railway automatically:
✅ Provisions SSL certificates
✅ Renews certificates before expiry
✅ Redirects HTTP → HTTPS
✅ Sets HSTS headers

No manual configuration needed!
```

### 8.2 Verify Certificate

```bash
# Check certificate validity
curl -v https://tryclariq.com 2>&1 | grep "certificate"

# Should show:
# Server certificate:
#   subject: CN=tryclariq.com
#   issuer: CN=R3,O=Let's Encrypt,C=US
#   valid from: ... 
#   valid until: ...
```

---

## 📊 Step 9: Setup Monitoring & Alerts

### 9.1 Railway Built-in Monitoring

```
Railway Dashboard:
1. Go to Logs tab
2. Set up log alerts
3. Set up metric alerts:
   - High CPU (>80%)
   - High memory (>90%)
   - High response time (>1s)
   - Deployment failed
```

### 9.2 External Monitoring (Sentry)

```bash
# Optional: Add error tracking
1. Create Sentry account (sentry.io)
2. Create new project: Python
3. Copy SENTRY_DSN
4. Add to Railway variables: SENTRY_DSN=...
5. Update main.py to initialize Sentry

# In main.py:
import sentry_sdk
sentry_sdk.init(os.getenv("SENTRY_DSN"))
```

---

## 🚀 Step 10: First Deployment Checklist

```
✅ GitHub repository connected to Railway
✅ Environment variables configured
✅ Dockerfile build successful
✅ Application starts without errors
✅ Health endpoint responds (/api/health)
✅ Dashboard loads (https://tryclariq.com)
✅ API endpoints working
✅ DNS records pointing to Railway
✅ SSL certificate valid
✅ HTTPS redirect working
✅ Database connected
✅ Logs showing no errors
✅ Monitoring/alerts configured
```

---

## 📈 Production Configuration

### Web Service Settings

```
In Railway Dashboard → Settings:

Build Command:
  (uses Dockerfile)

Start Command:
  gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000

Port:
  8000

Healthcheck:
  /api/health
```

### Scaling

```
Railway automatically:
- Scales to handle traffic
- Distributes across multiple instances
- Handles load balancing
- No manual configuration needed

Upgrade plan to scale:
- Railway Hobby: $5/month (1 instance)
- Railway Team: Custom pricing (auto-scaling)
```

---

## 🔧 Troubleshooting

### Build Failed

```bash
# Check Railway logs:
1. Dashboard → Deployments
2. Find failed deployment
3. Click to view logs
4. Look for error message

Common issues:
- Missing environment variables → Add in Variables tab
- Port mismatch → Ensure port 8000 in Dockerfile
- Dependencies not installed → Check requirements.txt
```

### Application Won't Start

```bash
# Check logs for:
1. Import errors → Missing packages
2. Database errors → Check DATABASE_URL
3. Permission errors → Check file permissions

Solution:
1. Fix the issue locally
2. Push to GitHub
3. Railway auto-redeploys
```

### Domain Not Resolving

```bash
# Wait for DNS propagation (up to 24 hours)
# Check with:
dig tryclariq.com +short
# Should return Railway IP/CNAME

# In Railway:
1. Go to Deployments → Settings
2. Verify custom domain listed
3. Check domain status (green = working)
```

### Slow Response Times

```bash
# Check metrics in Railway:
1. Deployments → Metrics
2. Look for high CPU/memory
3. Solutions:
   - Upgrade plan (more resources)
   - Optimize database queries
   - Add caching (Redis)
```

---

## 💰 Pricing

| Plan | Price | Features |
|------|-------|----------|
| Hobby | Free | 1 service, 100 hours/month |
| Pro | $5/month | Unlimited services, full month |
| Team | Custom | Auto-scaling, dedicated support |

**Estimated cost for CLARIQ:**
- Development: Free (Hobby plan)
- Production: $5-20/month (Pro plan)

---

## 📞 Support & Monitoring

### Railway Support

```
Dashboard:
- Settings → Support
- Submit issue directly
- Response time: 1-4 hours

Community:
- Discord: railway.app/discord
- GitHub: railway/issues
```

### Application Monitoring

```
# View logs
Railway Dashboard → Logs tab

# Real-time metrics
Railway Dashboard → Metrics tab

# Error tracking (optional)
Sentry Dashboard for detailed errors
```

---

## 🎉 After Deployment

1. ✅ Test all endpoints
2. ✅ Setup third-party integrations (Stripe, Slack, etc)
3. ✅ Configure backups
4. ✅ Setup monitoring & alerts
5. ✅ Document deployment process
6. ✅ Plan scaling strategy

---

## 📚 Next Steps

- [DNS_SETUP.md](DNS_SETUP.md) - Complete domain configuration
- [DOMAIN_CHECKLIST.md](DOMAIN_CHECKLIST.md) - Production readiness
- [DEPLOYMENT.md](DEPLOYMENT.md) - Alternative deployment platforms
- [README.md](README.md) - Project overview

---

**Total Setup Time: 10-15 minutes**

✅ Your CLARIQ platform is now live at https://tryclariq.com!

Questions? Check Railway docs: https://docs.railway.app
