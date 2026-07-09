# Render Deployment Checklist

## ✅ Your GitHub is Connected!

Now complete these steps on Render dashboard:

---

## **Step 1: Finish Service Configuration**

On Render dashboard for your service, verify these are set:

```
Name:              clariq-api
Environment:       Python 3
Region:            Oregon  
Branch:            main
Build Command:     pip install -r backend/requirements.txt
Start Command:     cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
Instance Type:     Starter
```

---

## **Step 2: Add Environment Variables**

In Render dashboard → **Environment** section, add these variables:

```
DATABASE_URL=sqlite:///./data/clariq.db
JWT_SECRET=fpZauHy00sDYFakpi2OKod9sgRD4UAMaAv7n6TOmgRw
ENVIRONMENT=production
PYTHONUNBUFFERED=1
```

Optional (leave blank if not ready):
```
SHOPIFY_API_KEY=
SHOPIFY_API_SECRET=
ANTHROPIC_API_KEY=
SNOWFLAKE_ACCOUNT=
```

---

## **Step 3: Deploy**

Click **"Create Web Service"** (or if already in service, save changes to trigger build)

**Build status:**
- 🔵 "Building..." → Wait 2-3 minutes
- ✅ "Building succeeded" → Service is live!
- ❌ "Building failed" → Check logs for errors

---

## **Step 4: Get Your Live URL**

Once "Live" status appears, Render gives you a URL like:

```
https://clariq-api.onrender.com
```

**Save this URL!** You'll need it next.

---

## **Step 5: Test API**

```bash
curl https://YOUR_RENDER_URL/api/health
```

Should return:
```json
{"api":"healthy","snowflake":"connected"}
```

---

## **Step 6: Share URL**

Once deployed and tested, reply with:
```
Render URL: https://clariq-api.onrender.com
```

Then I'll:
1. ✅ Update frontend API configuration
2. ✅ Test all endpoints
3. ✅ Set up custom domain
4. ✅ Configure email/SMTP
5. ✅ Launch!

---

**Status:** Waiting for Render deployment ⏳
