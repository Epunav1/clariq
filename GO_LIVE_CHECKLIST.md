# 🎯 CLARIQ Go-Live Checklist

**Complete this before launching https://tryclariq.com**

---

## ✅ Phase 1: Pre-Launch Verification (5 min)

### Code Quality
- [ ] No syntax errors: `python -m py_compile backend/main.py`
- [ ] No import errors: `python -c "from main import app; print('✅ OK')"`
- [ ] Git status clean: `git status` shows "nothing to commit"
- [ ] Latest commit pushed: `git log -1` shows recent work
- [ ] No secrets in code: `grep -r "sk_" backend/` returns nothing sensitive

### Documentation Review
- [ ] README.md reviewed
- [ ] API_DOCUMENTATION.md complete
- [ ] PRODUCTION_LAUNCH.md understood
- [ ] FAQ.md ready for users
- [ ] FEEDBACK_SETUP.md reviewed

### Environment Prep
- [ ] `.env.production.example` has all 50+ variables
- [ ] No hardcoded secrets in code
- [ ] JWT_SECRET placeholder ready to generate
- [ ] Database path configured
- [ ] Log level set to INFO (not DEBUG)

**Status: [  ] Ready to proceed**

---

## ✅ Phase 2: Railway Deployment (10 min)

### 2.1 GitHub Repository
- [ ] Latest code pushed to main branch
- [ ] No uncommitted changes: `git status` clean
- [ ] Branch protection enabled (GitHub → Settings → Branches)
- [ ] No merge conflicts
- [ ] All tests passing locally (if applicable)

```bash
# Verify
git status
git log -1
```

### 2.2 Railway Account Setup
- [ ] Railway account created at railway.app
- [ ] GitHub authorized for Railway
- [ ] New project created
- [ ] Epunav1/clariq repository selected

### 2.3 Environment Variables
- [ ] Copy `.env.production.example` to Railway Variables tab
- [ ] **CRITICAL VARIABLES SET:**
  ```
  ✓ ENVIRONMENT=production
  ✓ DEBUG=false
  ✓ BACKEND_URL=https://api.tryclariq.com
  ✓ FRONTEND_URL=https://tryclariq.com
  ✓ CORS_ORIGINS=https://tryclariq.com,https://www.tryclariq.com
  ✓ DATABASE_URL=sqlite:///./data/clariq.db (or PostgreSQL)
  ✓ JWT_SECRET=<generate random secret>
  ```

- [ ] Generate JWT_SECRET:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
  Copy output to Railway: JWT_SECRET=...

- [ ] All integration keys set (if configured):
  ```
  ✓ STRIPE_SECRET_KEY
  ✓ STRIPE_PUBLISHABLE_KEY
  ✓ SLACK_BOT_TOKEN
  ✓ SMTP_USER
  ✓ SMTP_PASSWORD
  ✓ OWNER_EMAIL
  ```

### 2.4 Railway Build & Deploy
- [ ] Build log shows no errors: `docker build successful`
- [ ] Application starts: logs show app running
- [ ] Public URL generated: `something.railway.app`
- [ ] Health endpoint responds: `/api/health` returns 200

```bash
# Test (once deployed)
curl https://yourproject.railway.app/api/health
# Expected: {"status": "ok"}
```

**Deployment Status: [  ] Complete and Verified**

---

## ✅ Phase 3: Domain Configuration (15 min)

### 3.1 DNS Records
At your domain registrar (GoDaddy, Namecheap, Route53, etc):

```
RECORD 1: Main Domain
Type:   A or CNAME
Name:   tryclariq.com (or @)
Value:  <Railway public URL or IP>
TTL:    300

RECORD 2: WWW Subdomain
Type:   CNAME
Name:   www
Value:  tryclariq.com
TTL:    300

RECORD 3: API Subdomain
Type:   CNAME
Name:   api
Value:  tryclariq.com
TTL:    300
```

- [ ] DNS records added
- [ ] Registrar shows changes saved
- [ ] Screenshot taken (for reference)

### 3.2 Railway Custom Domain
In Railway Dashboard:
1. Go to Deployments → Settings
2. Add Custom Domain: `tryclariq.com`
3. Railway verifies ownership
4. Status shows "Active" (green)

- [ ] Custom domain added to Railway
- [ ] Status shows Active
- [ ] SSL certificate provisioned (auto)

### 3.3 DNS Propagation (wait 5-15 minutes)
```bash
# Check every 2 minutes
dig tryclariq.com +short
# Should return Railway IP or CNAME

# Use public DNS if local cache stale
dig @8.8.8.8 tryclariq.com +short
```

- [ ] DNS resolves: `dig tryclariq.com` returns IP/CNAME
- [ ] Propagation complete globally

**DNS Status: [  ] Live and Propagated**

---

## ✅ Phase 4: Verification (10 min)

### 4.1 HTTPS & Certificate
```bash
# Verify HTTPS works
curl -I https://tryclariq.com
# Expected: HTTP/2 200 or 301

# Check certificate
openssl s_client -connect tryclariq.com:443 </dev/null 2>/dev/null | grep "subject\|issuer"
# Expected: CN=tryclariq.com, issuer: Let's Encrypt
```

- [ ] HTTPS works: `curl https://tryclariq.com` returns 200/301
- [ ] SSL certificate valid: no warnings
- [ ] Certificate issuer: Let's Encrypt
- [ ] HSTS header present: `Strict-Transport-Security`

### 4.2 Dashboard Access
```bash
open https://tryclariq.com
```

- [ ] Dashboard loads without errors
- [ ] No console errors (F12 → Console)
- [ ] No network errors (F12 → Network)
- [ ] All assets loading (CSS, JS, images)
- [ ] Dark mode button works
- [ ] UI responsive on mobile

### 4.3 API Endpoints
```bash
# Health check
curl https://api.tryclariq.com/api/health
# Expected: {"status": "ok"}

# List pilots (may be empty)
curl -H "Authorization: Bearer test" https://api.tryclariq.com/api/pilot
# Expected: [] or pilot list

# Test with main domain
curl https://tryclariq.com/api/health
# Expected: {"status": "ok"}
```

- [ ] Health endpoint responds: /api/health → 200
- [ ] API endpoints accessible
- [ ] CORS headers present
- [ ] API subdomain works: api.tryclariq.com

### 4.4 Security Headers
```bash
curl -I https://tryclariq.com | grep -i "strict-transport-security\|x-frame-options\|x-content-type-options"
```

- [ ] HSTS header: `max-age=31536000`
- [ ] X-Frame-Options: `SAMEORIGIN`
- [ ] X-Content-Type-Options: `nosniff`
- [ ] No mixed content warnings

**Verification Status: [  ] All Checks Passed**

---

## ✅ Phase 5: Post-Launch Setup (15 min)

### 5.1 Stripe Configuration
```bash
# Login to https://dashboard.stripe.com
# Test mode → API Keys

1. Get API Keys:
   - Secret Key: sk_test_... → Add to STRIPE_SECRET_KEY
   - Publishable Key: pk_test_... → Add to STRIPE_PUBLISHABLE_KEY

2. Setup Webhooks:
   - Dashboard → Webhooks
   - Add endpoint: https://api.tryclariq.com/api/billing/webhook
   - Events: customer.subscription.*, invoice.*

3. Redeploy with new keys:
   - Railway: Add STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY
   - Wait for redeploy to complete

4. Test payment:
   - Use card: 4242 4242 4242 4242
   - Expiry: Any future date
   - CVC: Any 3 digits
```

- [ ] Stripe API keys configured
- [ ] Webhook endpoint added
- [ ] Test payment successful
- [ ] Railway redeployed

### 5.2 Email (Feedback System)
```bash
# Gmail Example:
1. Enable 2FA: https://myaccount.google.com/security
2. Create App Password:
   https://myaccount.google.com/apppasswords
   - Select: Mail
   - Select: Windows (or custom)
   - Copy 16-char password

3. Add to Railway:
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=<16-char-app-password>
   OWNER_EMAIL=your-email@gmail.com

4. Test feedback:
   curl -X POST https://api.tryclariq.com/api/feedback/submit \
     -H "Content-Type: application/json" \
     -d '{
       "user_email": "test@example.com",
       "subject": "Test feedback",
       "message": "This is a test feedback message"
     }'

5. Verify: Check OWNER_EMAIL for notification
```

- [ ] SMTP credentials configured
- [ ] Test feedback submitted
- [ ] Owner received notification email
- [ ] User received confirmation email

### 5.3 Slack Integration (Optional)
```bash
# Setup Slack Bot:
1. Go to https://api.slack.com/apps
2. Create New App → From scratch
3. Name: CLARIQ Bot
4. Workspace: Select your workspace
5. OAuth & Permissions → Scopes:
   - chat:write
   - commands
6. Install to workspace
7. Copy Bot Token: xoxb-...

# Add to Railway:
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL=#alerts

# Test:
curl -X POST https://api.tryclariq.com/api/integrations/slack/alert \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test alert from CLARIQ",
    "channel": "#alerts"
  }'
```

- [ ] Slack app created
- [ ] Bot token configured
- [ ] Test message sent
- [ ] Message appeared in Slack

### 5.4 Google Sheets (Optional)
```bash
# Setup Google Service Account:
1. https://console.cloud.google.com
2. Create project: CLARIQ
3. APIs → Enable: Google Sheets API
4. Service Accounts → Create service account
5. Keys → Add key → JSON
6. Download JSON file

# Add to Railway:
GOOGLE_SHEETS_CREDENTIALS={<paste entire JSON>}
GOOGLE_SHEETS_SPREADSHEET_ID=<your-spreadsheet-id>

# Get spreadsheet ID:
# Open spreadsheet in Google Sheets
# URL: docs.google.com/spreadsheets/d/[ID_HERE]/edit
```

- [ ] Google service account created
- [ ] JSON credentials added
- [ ] Spreadsheet ID configured
- [ ] Share spreadsheet with service account email

### 5.5 Shopify Webhooks (Optional)
```bash
# In Shopify Admin:
1. Settings → Apps and Integrations → Webhooks
2. Create webhook:
   - Topic: Order created, Order updated
   - URL: https://api.tryclariq.com/api/shopify/webhook/orders
3. Create webhook:
   - Topic: Product updated, Customer created
   - URL: https://api.tryclariq.com/api/shopify/webhook/customers
4. Test webhook (Shopify provides test button)
5. Verify: Check Railway logs
```

- [ ] Shopify webhooks registered
- [ ] Test webhooks passed
- [ ] Railway logs show webhook received
- [ ] Data syncing (if applicable)

**Post-Launch Status: [  ] All Integrations Configured**

---

## 🎯 Final Launch Checklist

### System Status
- [ ] Application responding at https://tryclariq.com
- [ ] API responding at https://api.tryclariq.com
- [ ] Dashboard loads without errors
- [ ] HTTPS/SSL working
- [ ] All security headers present

### Functionality
- [ ] Create/list pilots working
- [ ] ROI calculations working
- [ ] Analytics loading
- [ ] Export feature working
- [ ] Feedback system ready

### Monitoring
- [ ] Logs accessible in Railway
- [ ] Health check endpoint responding
- [ ] Performance metrics visible
- [ ] Errors being tracked
- [ ] Backups scheduled (if using PostgreSQL)

### Support
- [ ] Feedback email notifications working
- [ ] User confirmation emails working
- [ ] Support documentation published
- [ ] FAQ accessible to users
- [ ] Support email configured

### Security
- [ ] No test data in production
- [ ] No debug mode enabled
- [ ] Secrets not exposed
- [ ] Rate limiting active
- [ ] CORS properly configured

**Final Status: [  ] READY FOR PRODUCTION**

---

## 🚀 Launch Execution

When you're ready to go live:

```bash
# 1. Verify everything above is checked ✓
# 2. Take screenshot of Railway dashboard (for reference)
# 3. Take screenshot of DNS records (for reference)
# 4. Announce to early users: 

"CLARIQ is now LIVE at https://tryclariq.com! 🚀

Features:
✅ Advanced ROI Analytics
✅ Predictive Forecasting
✅ Real-time Integrations
✅ Dark Mode Dashboard
✅ Feedback System (📬 contact us anytime)

Ready to optimize your pilot programs?
https://tryclariq.com"

# 5. Monitor for first 24 hours
#    - Check logs every hour
#    - Monitor for error spikes
#    - Respond to feedback quickly
```

---

## 📊 Launch Day Timeline

```
T-1 Hour:  Final verification (Phase 4)
T-0:       Announce launch
T+30min:   Check for any critical errors
T+2hr:     First user test pilots
T+4hr:     Monitor stability
T+24hr:    Review logs and feedback
```

---

## 🆘 Troubleshooting Quick Links

**DNS not resolving?** → See DNS_SETUP.md troubleshooting
**SSL certificate invalid?** → Wait 15 min, Railway auto-renews
**API returning 500?** → Check Railway logs for error
**Emails not sending?** → Verify SMTP credentials in env vars
**Slow response?** → Check Railway metrics, upgrade if needed

---

## ✨ Success Criteria

You're live when:

✅ https://tryclariq.com loads instantly  
✅ https://api.tryclariq.com/api/health returns 200  
✅ Dashboard displays correctly  
✅ No console errors  
✅ HTTPS green lock showing  
✅ Feedback emails working  
✅ User support system ready  
✅ Monitoring alerts active  

---

## 📝 Sign-Off

- [ ] I have verified all items above
- [ ] System is production-ready
- [ ] Team notified of go-live
- [ ] Monitoring dashboard open
- [ ] Support email monitored

**Checked by:** ___________________  
**Date:** _______________________  
**Time:** _______________________  

---

**CLARIQ is now LIVE! 🎉**

Monitor dashboard, respond to feedback, and celebrate! 🚀
