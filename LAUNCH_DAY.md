# 🚀 CLARIQ Launch Day Playbook

**Real-time step-by-step guide for production launch**

---

## 🕐 Timeline: ~1 Hour Total

```
T-30min: Preparation
T-0min:  Start deployment
T+10min: Railway app deployed
T+15min: Domain setup complete
T+25min: Verification complete
T+40min: Integrations configured
T+55min: Post-launch setup done
T+60min: LIVE! 🎉
```

---

## 📋 Before You Start

### Have Ready:
- [ ] GitHub account logged in
- [ ] Railway.app account (or create new)
- [ ] Domain registrar account (GoDaddy, Namecheap, Route53, etc)
- [ ] SMTP credentials ready (Gmail app password or SendGrid)
- [ ] Stripe account + API keys (test mode)
- [ ] `.env.production.example` opened
- [ ] GO_LIVE_CHECKLIST.md printed/open

### Systems:
- [ ] Stable internet connection
- [ ] Terminal open and ready
- [ ] Browser with 2+ tabs
- [ ] Monitor email for confirmations

---

## ✅ T-30min: Preparation Phase

### Step 1: Run Pre-Flight Checks (5 min)

```bash
cd /Users/ebubeepuna/Downloads/clariq

# Run verification script
bash scripts/pre_flight_check.sh

# Expected output:
# ✓ ALL CHECKS PASSED - READY FOR DEPLOYMENT
```

**If failures:** Fix issues shown and re-run until all pass.

**If passes:** Continue to Step 2.

### Step 2: Verify Git Status (2 min)

```bash
# Check that latest code is pushed
git log -1 --oneline
# Should show recent commit with all your work

# Verify no uncommitted changes
git status
# Should show: "On branch main" and "nothing to commit"

# If changes exist:
git add -A
git commit -m "final: Pre-launch preparation"
git push origin main
```

### Step 3: Generate JWT Secret (1 min)

```bash
# Generate random secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Output will be something like:
# AZ_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p

# SAVE THIS - You'll need it in Step 5
```

### Step 4: Prepare Configuration (2 min)

```bash
# Open environment template
cat .env.production.example | head -20

# Note the required variables:
# - ENVIRONMENT=production
# - BACKEND_URL=https://api.tryclariq.com
# - FRONTEND_URL=https://tryclariq.com
# - JWT_SECRET=<your-generated-secret>
# - Database config
# - SMTP settings
# - Stripe keys (if using billing)
# - Owner email for feedback
```

**Status: [  ] Preparation Complete**

---

## ✅ T-0min: Railway Deployment Phase

### Step 5: Create Railway Project (5 min)

**In browser:**

```
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize GitHub if needed
5. Select: Epunav1/clariq
6. Click "Deploy Now"
```

**Wait 2-3 minutes for initial deploy...**

```
Expected in Railway Dashboard:
✓ Service: backend
✓ Status: Running (green)
✓ Logs: "Application startup complete"
```

### Step 6: Add Environment Variables (5 min)

**In Railway Dashboard:**

```
1. Go to your project
2. Click "Variables" tab
3. Click "Add Variable"
4. Add these critical variables:

Required:
  ENVIRONMENT → production
  DEBUG → false
  BACKEND_URL → https://api.tryclariq.com
  FRONTEND_URL → https://tryclariq.com
  CORS_ORIGINS → https://tryclariq.com,https://www.tryclariq.com
  JWT_SECRET → <paste your generated secret>

Database:
  DATABASE_URL → sqlite:///./data/clariq.db (or PostgreSQL)

Email (Feedback System):
  SMTP_HOST → smtp.gmail.com
  SMTP_PORT → 587
  SMTP_USER → your-email@gmail.com
  SMTP_PASSWORD → your-app-password
  SMTP_FROM → noreply@tryclariq.com
  OWNER_EMAIL → you@example.com

Integrations (Optional - add only if configured):
  STRIPE_SECRET_KEY → sk_test_...
  STRIPE_PUBLISHABLE_KEY → pk_test_...
  SLACK_BOT_TOKEN → xoxb-...
```

**After adding all variables:**

```
1. Railway auto-redeploys when variables change
2. Wait 3-5 minutes for redeploy to complete
3. Check logs: Should show no errors
4. Look for: "Application startup complete"
```

### Step 7: Get Public URL (1 min)

**In Railway Dashboard:**

```
1. Go to Deployments
2. Look for public URL (something.railway.app)
3. Test it: curl https://something.railway.app/api/health
4. Expected: {"status": "ok"}
5. SAVE THIS URL - You'll need it for domain setup
```

**Status: [  ] Railway Deployment Complete**

---

## ✅ T+15min: Domain Setup Phase

### Step 8: Configure DNS Records (10 min)

**At your domain registrar (GoDaddy, Namecheap, Route53, etc):**

```
1. Login to your registrar
2. Go to Domain Settings → DNS
3. Find "DNS Records" or "Manage DNS"
4. Add/Update these records:

RECORD 1 - Main Domain:
  Type: A or CNAME
  Name: @ (or tryclariq.com)
  Value: <Railway public URL or IP>
  TTL: 300
  Click Save

RECORD 2 - WWW:
  Type: CNAME
  Name: www
  Value: tryclariq.com
  TTL: 300
  Click Save

RECORD 3 - API:
  Type: CNAME
  Name: api
  Value: tryclariq.com
  TTL: 300
  Click Save
```

**Wait 2-3 minutes, then test:**

```bash
# Check DNS propagation
dig tryclariq.com +short
# Should return IP or CNAME

# If DNS not resolved yet, check with Google's DNS:
dig @8.8.8.8 tryclariq.com +short

# If still not showing, wait another 2 minutes and retry
```

### Step 9: Add Custom Domain to Railway (2 min)

**In Railway Dashboard:**

```
1. Go to your project → Deployments → Settings
2. Find "Custom Domain"
3. Click "Add Domain"
4. Enter: tryclariq.com
5. Railway verifies ownership (DNS records you just added)
6. Status should show: "Active" (green)
7. SSL certificate auto-provisioned
```

**Status: [  ] Domain Setup Complete**

---

## ✅ T+25min: Verification Phase

### Step 10: Verify HTTPS & SSL (5 min)

```bash
# Check HTTPS works
curl -I https://tryclariq.com
# Expected: HTTP/2 200 or 301 (redirect to HTTPS)

# Check certificate
openssl s_client -connect tryclariq.com:443 </dev/null 2>/dev/null | grep "subject="
# Expected: CN=tryclariq.com

# Check HSTS header
curl -I https://tryclariq.com | grep -i "strict-transport-security"
# Expected: strict-transport-security: max-age=31536000
```

### Step 11: Test API Endpoints (3 min)

```bash
# Health check
curl https://api.tryclariq.com/api/health
# Expected: {"status": "ok"}

# With main domain
curl https://tryclariq.com/api/health
# Expected: {"status": "ok"}

# Feedback system
curl -X POST https://api.tryclariq.com/api/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "test@example.com",
    "subject": "Test",
    "message": "Testing feedback system"
  }'
# Expected: {"feedback_id": 1, "status": "received"}

# Check support status
curl https://api.tryclariq.com/api/support/status
# Expected: {"status": "operational"}
```

### Step 12: Load Dashboard (2 min)

**In browser:**

```
1. Open https://tryclariq.com
2. Check for:
   ✓ Page loads quickly
   ✓ No console errors (F12 → Console)
   ✓ All images/CSS loaded (F12 → Network)
   ✓ No red error indicators
   ✓ Dashboard displays correctly
   ✓ Dark mode button works
   ✓ Mobile responsive (reduce window width)
```

**Status: [  ] Verification Complete**

---

## ✅ T+40min: Integration Setup Phase

### Step 13: Email Configuration (10 min)

**Gmail Setup (Recommended):**

```bash
# 1. Go to https://myaccount.google.com/security
# 2. Enable 2-Factor Authentication if not already enabled
# 3. Go to https://myaccount.google.com/apppasswords
# 4. Select: Mail
# 5. Select: Windows (or custom device)
# 6. Copy the 16-character password

# Now update Railway variables:
# In Railway Dashboard → Variables:
#   SMTP_USER=your-email@gmail.com
#   SMTP_PASSWORD=<16-char-password-from-above>
#   OWNER_EMAIL=your-email@gmail.com

# Wait 2 minutes for redeploy

# 7. Test sending feedback:
curl -X POST https://api.tryclariq.com/api/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "your-email@gmail.com",
    "user_name": "Test User",
    "subject": "Testing email notifications",
    "message": "If you receive this email, feedback system is working!",
    "feedback_type": "general"
  }'

# 8. Check your email for:
#    - Confirmation email (to you@example.com with ticket #)
#    - Notification email (to OWNER_EMAIL about the feedback)
```

**Verify: [  ] Emails received successfully**

### Step 14: Stripe Configuration (Optional, 5 min)

**If using billing:**

```bash
# 1. Go to https://dashboard.stripe.com
# 2. Login to your Stripe account
# 3. Go to: Developers → API Keys
# 4. Copy:
#    - Secret Key: sk_test_...
#    - Publishable Key: pk_test_...
# 5. Add to Railway Variables:
#    STRIPE_SECRET_KEY=sk_test_...
#    STRIPE_PUBLISHABLE_KEY=pk_test_...
# 6. Wait for redeploy (2-3 min)
# 7. Test with card 4242 4242 4242 4242

# Configure Webhooks:
# 1. Go to: Developers → Webhooks
# 2. Add endpoint:
#    URL: https://api.tryclariq.com/api/billing/webhook
#    Events: customer.subscription.created, customer.subscription.updated, invoice.payment_succeeded
# 3. Click: Add Endpoint
```

**Verify: [  ] Stripe working**

### Step 15: Slack Integration (Optional, 5 min)

**If using Slack:**

```bash
# 1. Go to https://api.slack.com/apps
# 2. Click: Create New App → From scratch
# 3. App Name: CLARIQ Bot
# 4. Workspace: Select your workspace
# 5. Go to: OAuth & Permissions
# 6. Scopes → Add:
#    - chat:write
#    - commands
# 7. Install to Workspace
# 8. Copy: Bot Token (starts with xoxb-)
# 9. Add to Railway Variables:
#    SLACK_BOT_TOKEN=xoxb-...
# 10. Wait for redeploy (2-3 min)
# 11. Test:
curl -X POST https://api.tryclariq.com/api/integrations/slack/alert \
  -H "Content-Type: application/json" \
  -d '{
    "message": "CLARIQ is now LIVE!"
  }'
```

**Verify: [  ] Message appeared in Slack**

**Status: [  ] Integrations Configured**

---

## ✅ T+55min: Post-Launch Setup

### Step 16: Final System Check (5 min)

```bash
# Check all systems responding
echo "API Health:"
curl -s https://api.tryclariq.com/api/health | python -m json.tool

echo ""
echo "Support Status:"
curl -s https://api.tryclariq.com/api/support/status | python -m json.tool

echo ""
echo "Railway Logs (check for errors):"
# Go to Railway Dashboard and review recent logs
# Should show: "Application startup complete" and no errors
```

### Step 17: Monitoring Setup

**Set up monitoring:**

```bash
# 1. Go to Railway Dashboard
# 2. Enable notifications:
#    - Settings → Notifications
#    - Add email for alerts
# 3. Set performance alerts:
#    - Monitor: CPU, Memory, Disk
#    - Alert if: > 80% usage
# 4. Monitor logs daily (first week)
```

**Status: [  ] Monitoring Active**

---

## 🎉 T+60min: GO LIVE!

### Step 18: Launch Announcement

**Send to users:**

```
🚀 CLARIQ IS NOW LIVE!

We're excited to announce CLARIQ is now available at:
https://tryclariq.com

✨ What You Can Do:
✓ Advanced ROI analytics for your pilot programs
✓ Real-time performance tracking
✓ Predictive forecasting (30/60/90 day outlook)
✓ Integration with Shopify, Stripe, Slack
✓ Dark mode dashboard
✓ Comprehensive reporting

📞 Need Help?
Use the "Send Feedback" button in the dashboard to:
- Report bugs
- Request features
- Ask for support
- Share complaints

Response time: 24 hours

🔗 Start here: https://tryclariq.com

Questions? Check our FAQ: https://tryclariq.com/faq

Happy analyzing! 🚀
```

### Step 19: Monitor First 24 Hours

```
Every 4 hours, check:
□ https://tryclariq.com loads
□ https://api.tryclariq.com/api/health returns 200
□ Railway logs show no errors
□ Email notifications working
□ No 500 errors in logs
□ Response time < 500ms
```

### Step 20: Celebrate! 🎉

You're live! Document what worked:

```bash
# Take final screenshot of:
1. Dashboard at https://tryclariq.com
2. Railway deployment dashboard
3. Domain DNS records
4. API health check response

# Create a "Launch Summary" with:
- Date/time of launch
- Environment details (Railway URL, domain, region)
- Initial metrics (uptime, response time)
- Known issues (if any)
- Next steps/roadmap

# Share success:
git log -1 --oneline
# Shows your launch commit in history
```

---

## 🆘 Troubleshooting During Launch

### "DNS not resolving"
```bash
# Wait 5-10 minutes
# Check with: dig tryclariq.com +short
# If still not working: Verify records match exactly
```

### "API returns 500 error"
```bash
# Check Railway logs for error message
# Common issues:
# - Missing environment variable
# - Database permission error
# - Dependency not installed
# Look at exact error in logs and fix
```

### "Emails not sending"
```bash
# Verify in Railway Variables:
# - SMTP_HOST correct
# - SMTP_USER correct
# - SMTP_PASSWORD correct (Gmail app password, not regular password)
# - OWNER_EMAIL valid
# Test: curl /api/support/status should show "email_service: configured"
```

### "SSL certificate not valid"
```bash
# Railway auto-provisions Let's Encrypt
# Takes 5-15 minutes after custom domain added
# Wait 15 minutes, then retry: openssl s_client -connect tryclariq.com:443
```

### "CORS errors in dashboard"
```bash
# Verify in .env.production.example:
# CORS_ORIGINS includes your domain
# Example: https://tryclariq.com,https://www.tryclariq.com
# Update in Railway Variables and redeploy
```

---

## ✅ Launch Complete When:

- [x] https://tryclariq.com loads instantly
- [x] https://api.tryclariq.com/api/health returns 200
- [x] SSL certificate valid (green lock)
- [x] Dashboard displays correctly
- [x] No console errors
- [x] Feedback system working (emails received)
- [x] Monitoring dashboard shows green
- [x] Railway logs show no critical errors
- [x] Team notified of go-live
- [x] User support ready (monitoring email)

---

## 📊 Post-Launch Checklist

**First Week:**
- [ ] Monitor dashboard daily
- [ ] Respond to user feedback <24hr
- [ ] Check error logs daily
- [ ] Verify backups running
- [ ] Review performance metrics

**First Month:**
- [ ] User feedback analysis
- [ ] Feature requests review
- [ ] Performance optimization
- [ ] Security audit
- [ ] Scaling assessment

---

## 🎯 Success!

**CLARIQ is now live at https://tryclariq.com** 🚀

Monitor, respond to users, and keep improving! 💪
