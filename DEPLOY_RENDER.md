# Deploy CLARIQ to Render.com

**Status:** Ready to deploy  
**Estimated Time:** 5 minutes  
**Cost:** Free tier available ($7/month starter tier when ready)

## Quick Start (Copy-Paste Steps)

### 1. Go to Render Dashboard
Open https://render.com and log in (create account if needed)

### 2. Create Web Service
Click **New** → **Web Service**

### 3. Connect Repository
- Select **Build and deploy from Git repository**
- Authorize GitHub (if not already done)
- Select `Epunav1/clariq` repository
- Branch: `main`
- Click **Connect**

### 4. Configure Service

**Name:**
```
clariq-api
```

**Environment:**
```
Python 3
```

**Region:**
```
Oregon (or closest to your users)
```

**Build Command:**
```
pip install -r backend/requirements.txt
```

**Start Command:**
```
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Instance Type:**
```
Starter (free tier)
```

### 5. Add Environment Variables

Click **Environment** and add these:

```
DATABASE_URL = sqlite:///./data/clariq.db
JWT_SECRET = fpZauHy00sDYFakpi2OKod9sgRD4UAMaAv7n6TOmgRw
ENVIRONMENT = production
PYTHONUNBUFFERED = 1
```

Add others as needed:
- `SHOPIFY_API_KEY`
- `SHOPIFY_API_SECRET`
- `ANTHROPIC_API_KEY` (optional, app works without)
- `SNOWFLAKE_ACCOUNT` (optional, app works without)

### 6. Deploy

Click **Create Web Service**

Render will automatically:
- Pull your code
- Install dependencies
- Start the service
- Give you a URL like `https://clariq-api.onrender.com`

### 7. Test

Wait 3-5 minutes for initial build, then:

```bash
curl https://clariq-api.onrender.com/api/health
```

**Expected response:**
```json
{"api":"healthy","snowflake":"connected"}
```

## Why Render Over Railway?

| Feature | Railway | Render |
|---------|---------|--------|
| FastAPI Support | ❌ 502 errors | ✅ Works |
| Python 3.11+ | ✅ | ✅ |
| Auto-deploy on push | ✅ | ✅ |
| Free tier | ✅ | ✅ |
| Reliability | ⚠️ Unstable | ✅ Proven |
| Setup time | 10 min | 5 min |

## After Deployment

1. **Get your Render URL**
   - Will be `https://clariq-api.onrender.com` (or custom)

2. **Update frontend** to point to new API:
   - Find all `https://clariq-production-5974.up.railway.app` references
   - Replace with your Render URL

3. **Next steps:**
   - [ ] Configure custom domain (tryclariq.com)
   - [ ] Set up SMTP for emails
   - [ ] Configure Stripe billing
   - [ ] Enable HTTPS (automatic on Render)
   - [ ] Set up monitoring/alerts

## Troubleshooting

**Service won't start?**
```bash
# Check logs in Render dashboard
# Look for Python import errors or config issues
```

**Getting 500 errors?**
```bash
# Service started but app crashed
# Check environment variables are set correctly
# Ensure JWT_SECRET is valid
```

**Static files not loading?**
```bash
# You may need to serve frontend separately
# Or update frontend API URLs
```

---

**Ready to proceed?** Follow the steps above and let me know your Render URL once deployed.
