# 🚀 CLARIQ Production Launch Playbook

**Your step-by-step guide to launch tryclariq.com in production.**

---

## ⏱️ Timeline

- **30 minutes**: Complete setup
- **5-10 minutes**: Railway deployment
- **15-20 minutes**: DNS & SSL configuration
- **5 minutes**: Verification & testing

**Total: 1 hour to production**

---

## 🎯 Phase 1: Pre-Launch Verification (5 min)

### 1.1 Run Local Tests

```bash
cd backend
python -m pytest tests/test_api.py -v --tb=short
```

**Expected:** Majority of tests pass (some may have DB dependency)

### 1.2 Verify Code Quality

```bash
# Check for syntax errors
python -m py_compile main.py
python -m py_compile routes/*.py

# Check imports
python -c "from main import app; print('✅ App imports successfully')"
```

### 1.3 Review Environment Config

```bash
# Check .env.production.example has all needed variables
grep -c "=" .env.production.example
# Should have 50+ variables configured
```

---

## 🎯 Phase 2: Railway Deployment (10 min)

### 2.1 Push to GitHub

```bash
# Ensure all changes are committed
git status
git add -A
git commit -m "Deploy production version to Railway"
git push origin main
```

### 2.2 Connect Railway

```
1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project
4. Deploy from GitHub repo: Epunav1/clariq
5. Railway auto-builds and deploys
```

### 2.3 Configure Environment

```
In Railway Dashboard:
1. Go to Variables tab
2. Add all variables from .env.production.example:
   - ENVIRONMENT=production
   - DEBUG=false
   - BACKEND_URL=https://api.tryclariq.com
   - FRONTEND_URL=https://tryclariq.com
   - CORS_ORIGINS=https://tryclariq.com,https://www.tryclariq.com
   - (All other integration keys)

3. Redeploy after adding variables
```

### 2.4 Get Public URL

```
In Railway:
1. Deployments → Click active deployment
2. Copy public URL (something.railway.app)
3. Note this for DNS setup
```

---

## 🎯 Phase 3: Domain Setup (15 min)

### 3.1 Configure DNS

**At your domain registrar:**

```
Add these DNS records:

1. Main Domain
   Type:   CNAME
   Name:   tryclariq.com (or @)
   Value:  <railway-public-url>
   TTL:    300

2. WWW Subdomain
   Type:   CNAME
   Name:   www
   Value:  tryclariq.com
   TTL:    300

3. API Subdomain
   Type:   CNAME
   Name:   api
   Value:  tryclariq.com
   TTL:    300
```

### 3.2 Railway Custom Domain

```
In Railway Dashboard:
1. Deployments → Settings
2. Add Custom Domain
3. Enter: tryclariq.com
4. Click Add
5. Railway provisions SSL certificate (auto)
6. Status shows when ready (usually 5-10 min)
```

### 3.3 Verify DNS Propagation

```bash
# Wait 5-15 minutes for propagation
# Then verify:

dig tryclariq.com +short
# Should return Railway IP or CNAME

# Verify HTTPS works
curl -v https://tryclariq.com 2>&1 | grep "certificate\|200"
# Should show valid certificate and 200 OK
```

---

## 🎯 Phase 4: Verification (10 min)

### 4.1 Test Endpoints

```bash
# Health check
curl https://tryclariq.com/api/health
# Expected: {"status": "ok"}

# API endpoints
curl https://api.tryclariq.com/api/pilot
# Should return pilot data or empty list

# Dashboard
open https://tryclariq.com
# Should load the CLARIQ dashboard
```

### 4.2 SSL/Certificate Check

```bash
# Verify HTTPS is working
curl -I https://tryclariq.com
# Should show: HTTP/2 200 or 301 (redirect)
# Should have Security headers

# Check certificate
openssl s_client -connect tryclariq.com:443 </dev/null 2>/dev/null | grep "subject\|issuer\|CN="
# Should show: CN=tryclariq.com, issued by Let's Encrypt
```

### 4.3 CORS & Headers Check

```bash
# Verify CORS headers
curl -H "Origin: https://tryclariq.com" -I https://api.tryclariq.com/api/health
# Should have: Access-Control-Allow-Origin header

# Verify security headers
curl -I https://tryclariq.com | grep -i "strict-transport-security\|x-frame-options"
# Should show HSTS and X-Frame-Options headers
```

### 4.4 Browser Testing

```
1. Open https://tryclariq.com in browser
2. Check Console (F12 → Console) for JS errors
3. Check Network tab for all resources loading
4. Test dark mode toggle (if implemented)
5. Test filtering and bulk actions
6. Verify API calls working (Network tab)
```

---

## 🎯 Phase 5: Post-Launch Setup (15 min)

### 5.1 Configure Integrations

**Stripe:**
```
1. Get live API keys from Stripe Dashboard
2. Add to Railway variables:
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_PUBLISHABLE_KEY=pk_live_...
3. Update webhook endpoint in Stripe:
   https://api.tryclariq.com/api/billing/webhook
4. Redeploy
```

**Slack:**
```
1. Create Slack App at api.slack.com
2. Get Bot Token
3. Add to Railway: SLACK_BOT_TOKEN=xoxb-...
4. Set webhook URL if needed
5. Redeploy
```

**Google Sheets:**
```
1. Create service account in Google Cloud
2. Download JSON credentials
3. Add to Railway: GOOGLE_SHEETS_CREDENTIALS={...json...}
4. Add spreadsheet ID: GOOGLE_SHEETS_SPREADSHEET_ID=...
5. Redeploy
```

### 5.2 Setup Monitoring

```bash
# In Railway Dashboard:
1. Go to Logs tab
2. Set up alerts:
   - High CPU usage
   - High error rate
   - Deployment failures

# Optional: Sentry error tracking
1. Create account at sentry.io
2. Create Python project
3. Copy SENTRY_DSN
4. Add to Railway variables
5. Redeploy
```

### 5.3 Database Backups

```bash
# For production:
1. In Railway → Add Service → PostgreSQL
2. Replace SQLite DATABASE_URL with PostgreSQL
3. Redeploy
4. Backups auto-handled by Railway

# For SQLite:
# Use scripts/backup.sh with cron job
# (See DEPLOYMENT.md for details)
```

### 5.4 Documentation

```bash
# Ensure all docs are updated:
✅ README.md - Updated
✅ API_DOCUMENTATION.md - Deployed
✅ DEPLOYMENT.md - Reference
✅ DNS_SETUP.md - For domain config
✅ DOMAIN_CHECKLIST.md - For verification
✅ RAILWAY_DEPLOYMENT.md - Platform-specific guide
```

---

## 📊 Production Readiness Checklist

Before going live, verify:

### Infrastructure
- [ ] Application deployed to Railway
- [ ] Custom domain configured
- [ ] SSL certificate valid and auto-renewing
- [ ] DNS records propagated
- [ ] API responding on public URL
- [ ] Dashboard loading

### Configuration
- [ ] All environment variables set
- [ ] Database configured (SQLite or PostgreSQL)
- [ ] API endpoints accessible
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Security headers present

### Features
- [ ] User authentication working
- [ ] API endpoints functional
- [ ] Database operations successful
- [ ] File uploads working
- [ ] Email notifications enabled
- [ ] All routes responsive

### Security
- [ ] HTTPS enforced
- [ ] HSTS header enabled
- [ ] SQL injection prevention working
- [ ] CORS whitelist correct
- [ ] Secrets not exposed
- [ ] JWT tokens working

### Monitoring
- [ ] Application logs accessible
- [ ] Performance metrics visible
- [ ] Error tracking configured
- [ ] Alerts enabled
- [ ] Backup strategy in place
- [ ] Rollback procedure documented

### Third-Party
- [ ] Stripe webhook registered
- [ ] Shopify app authorized
- [ ] Slack bot token working
- [ ] Google Sheets credentials valid
- [ ] Email service configured
- [ ] All integrations tested

---

## 🚨 Troubleshooting

### App Won't Start

```bash
# Check Railway logs:
1. Dashboard → Deployments → Failed deployment
2. View build/runtime logs
3. Look for error messages

Common fixes:
- Missing environment variables
- Syntax errors in code
- Import errors
- Database connection failures
```

### DNS Not Resolving

```bash
# Troubleshoot:
dig tryclariq.com
# Should return Railway CNAME after 15 min

# If still not working:
1. Verify DNS records in registrar
2. Clear local DNS cache:
   - macOS: sudo dscacheutil -flushcache
   - Linux: sudo systemctl restart systemd-resolved
3. Wait another 15 minutes (DNS propagation)
4. Try public DNS: dig @8.8.8.8 tryclariq.com
```

### SSL Certificate Not Valid

```bash
# Check Railway status:
1. Dashboard → Deployments → Settings
2. Custom Domain shows status
3. Wait 5-10 minutes if just added

# If certificate expired:
1. Railway auto-renews before expiry
2. No manual action needed
3. If issues, rebuild deployment
```

### API Returning 500 Errors

```bash
# Check:
1. Railway logs for error details
2. Environment variables are set
3. Database connection working
4. All dependencies installed

Solutions:
1. Review error in logs
2. Fix code issue locally
3. Commit and push to GitHub
4. Railway auto-redeploys
```

---

## 📞 Support Resources

| Issue | Reference |
|-------|-----------|
| DNS Setup | [DNS_SETUP.md](DNS_SETUP.md) |
| Domain Config | [DOMAIN_CHECKLIST.md](DOMAIN_CHECKLIST.md) |
| Railway Deployment | [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) |
| All Platforms | [DEPLOYMENT.md](DEPLOYMENT.md) |
| API Reference | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) |
| General Setup | [README.md](README.md) |

---

## 🎉 Success Criteria

Your launch is successful when:

✅ https://tryclariq.com loads without errors  
✅ https://api.tryclariq.com/api/health returns 200  
✅ Dashboard displays correctly  
✅ SSL certificate is valid  
✅ HSTS headers present  
✅ All integrations working  
✅ Monitoring configured  
✅ Backups scheduled  

---

## 🔄 Post-Launch Workflow

1. **Week 1**: Monitor logs, fix any issues
2. **Week 2**: Onboard first pilots, gather feedback
3. **Week 3**: Iterate based on feedback
4. **Week 4**: Scale infrastructure if needed

---

**Your CLARIQ platform is production-ready!**

**Questions?** See [README.md](README.md) or specific deployment guide.

**Ready to launch?** Follow the phases above, 1 hour to production! 🚀
