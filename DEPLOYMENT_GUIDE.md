# 🚀 CLARIQ PRODUCTION DEPLOYMENT GUIDE

## Status: READY FOR LAUNCH

All backend code is production-ready. Follow these steps to go live on Render in **5 minutes**.

---

## 📋 STEP-BY-STEP DEPLOYMENT

### **Step 1: Create Render Account** (If needed)
- Go to https://render.com
- Sign up with GitHub (choose Epunav1 account)
- Skip for now if already connected

### **Step 2: Deploy Backend to Render**

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Select repository: **Epunav1/clariq**
4. Click **"Connect"**

### **Step 3: Configure Service**

Fill in the configuration form:

```
Name:              clariq-api
Environment:       Python 3
Region:            Oregon
Branch:            main

Build Command:
pip install -r backend/requirements.txt

Start Command:
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1

Instance Type:     Starter (Free tier)
```

### **Step 4: Add Environment Variables**

Click the **"Environment"** section and add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `sqlite:///./data/clariq.db` |
| `JWT_SECRET` | `fpZauHy00sDYFakpi2OKod9sgRD4UAMaAv7n6TOmgRw` |
| `ENVIRONMENT` | `production` |
| `PYTHONUNBUFFERED` | `1` |

### **Step 5: Deploy**

Click **"Create Web Service"**

**Watch the build:**
- 🔵 Building... (2-3 min)
- 🟢 Live (appears after build)

Once "Live" appears, Render assigns you a URL like:
```
https://clariq-api.onrender.com
```

---

## ✅ VERIFY DEPLOYMENT

### Test the API:

```bash
curl https://clariq-api.onrender.com/api/health
```

**Expected response:**
```json
{
  "status": "ok",
  "service": "CLARIQ API",
  "version": "0.4.0"
}
```

If you get this response: ✅ **Backend is live!**

---

## 🔄 UPDATE FRONTEND

Once you have your Render URL:

```bash
chmod +x update-frontend-urls.sh
./update-frontend-urls.sh https://clariq-api.onrender.com
```

This updates all frontend files to use your new API URL.

Then commit:
```bash
git add .
git commit -m "chore: Update API URLs to Render production endpoint"
```

---

## 📱 WHAT HAPPENS ON RENDER

### Build Phase (2-3 minutes)
- Checks out your code
- Installs dependencies from `backend/requirements.txt`
- Creates SQLite directory at `backend/data/`

### Start Phase (1-2 minutes)
- Runs: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`
- Sets environment variables
- Initializes FastAPI app
- Mounts all routers (/api/*)
- Starts background scheduler
- Ready to receive requests

### Production Phase (∞)
- Responds to HTTP requests
- Runs background sync jobs (Shopify, Amazon)
- Persists data to SQLite
- Logs to stdout (visible in Render dashboard)

---

## 🔧 TROUBLESHOOTING

### Build Fails?
1. Check Render logs (Dashboard → clariq-api → Logs)
2. Look for Python import errors
3. Verify all `requirements.txt` packages install correctly

### Service Crashes?
1. Render → clariq-api → Logs
2. Common issues:
   - Missing environment variables → Add them in Render dashboard
   - Port binding error → Render sets `$PORT` automatically
   - Import errors → Check `main.py` imports

### API Not Responding?
1. Verify service shows "Live" status (not "Building" or "Failed")
2. Test with `curl https://clariq-api.onrender.com/api/health`
3. Check that environment variables are set correctly
4. Wait 30 seconds after "Live" appears (warm-up time)

---

## 🎯 WHAT'S INCLUDED IN DEPLOYMENT

✅ **FastAPI Application**
- 18+ routers mounted at `/api/*`
- JWT authentication configured
- CORS enabled for tryclariq.com domains
- Health check endpoint

✅ **Background Services**
- APScheduler daemon (60min Shopify sync, 120min Amazon sync)
- Database persistence (SQLite)
- Job status tracking

✅ **Database**
- SQLite at `backend/data/clariq.db`
- Auto-created on first run
- Persists across deployments (Render's storage)

✅ **Optional Dependencies**
- Graceful fallback if Snowflake/Anthropic unavailable
- Returns 503 errors instead of crashing
- Core functionality works without them

---

## 📊 MONITORING

### View Logs:
```
Render Dashboard → clariq-api → Logs
```

Look for:
- ✅ "Application startup complete"
- ✅ Scheduler jobs executing
- ❌ Any ERROR messages

### Check Health:
```bash
curl https://clariq-api.onrender.com/api/health
```

### Manual Sync Trigger:
```bash
curl -X POST https://clariq-api.onrender.com/api/sync/all/now
```

---

## 🚀 POST-DEPLOYMENT

1. **Test all endpoints** with the test script:
   ```bash
   chmod +x test-api.sh
   ./test-api.sh https://clariq-api.onrender.com
   ```

2. **Update landing page** to point to new API URL

3. **Monitor logs** for first few minutes

4. **Set up custom domain** (optional, can do later)

5. **Configure email/SMTP** (optional, can do later)

---

## 📞 SUPPORT

If deployment fails:
1. Check Render logs first
2. Verify all environment variables are set
3. Confirm `backend/requirements.txt` has no syntax errors
4. Make sure Procfile uses correct command

---

## ✨ YOU'RE ALL SET!

Your CLARIQ backend is production-ready. Deploy to Render now and go live! 🎉

Need the Render URL? Get it from the Render dashboard once "Live" appears.

---

**Render URL:** `https://clariq-api.onrender.com` (replace with your actual URL)

**Frontend Update:** `./update-frontend-urls.sh https://clariq-api.onrender.com`

**Test:** `./test-api.sh https://clariq-api.onrender.com`
