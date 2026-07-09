# CLARIQ Platform - Frequently Asked Questions (FAQ)

**Last Updated:** July 2024  
**Version:** 2.0.0

---

## 🚀 Deployment & Launch

### Q: How long does it take to deploy to production?
**A:** About **1 hour total**:
- Railway deployment: 10 minutes
- DNS configuration: 15 minutes
- SSL setup: 5 minutes (automatic)
- Verification & testing: 10 minutes
- Integration setup: 20 minutes

See [PRODUCTION_LAUNCH.md](PRODUCTION_LAUNCH.md) for step-by-step guide.

---

### Q: Which deployment platform should I choose?
**A:** We recommend **Railway.app** for easiest setup:
- ✅ Auto-deploy from GitHub (5 min setup)
- ✅ Automatic HTTPS/SSL certificates
- ✅ Free tier available
- ✅ Simple environment management
- ✅ Built-in monitoring

**Alternatives:**
- **AWS ECS**: For enterprise/scale
- **DigitalOcean**: Good price/features balance
- **Docker Compose**: For self-hosted
- **Heroku**: Simple but pricier

See [DEPLOYMENT.md](DEPLOYMENT.md) for all options.

---

### Q: How do I configure my domain (tryclariq.com)?
**A:** Follow [DNS_SETUP.md](DNS_SETUP.md):

1. Add DNS records at your registrar:
   ```
   tryclariq.com    CNAME  railway-url
   www              CNAME  tryclariq.com
   api              CNAME  tryclariq.com
   ```

2. Configure custom domain in Railway

3. Railway auto-provisions SSL certificate

4. Wait 15 minutes for DNS propagation

See [DOMAIN_CHECKLIST.md](DOMAIN_CHECKLIST.md) for verification.

---

### Q: Will SSL/HTTPS be automatic?
**A:** **Yes, completely automatic:**
- Railway auto-provisions Let's Encrypt certificates
- Certificates auto-renew before expiry
- HTTP → HTTPS redirect auto-enabled
- HSTS headers auto-configured
- No manual SSL setup needed

---

### Q: What if deployment fails?
**A:** Check [PRODUCTION_LAUNCH.md](PRODUCTION_LAUNCH.md) troubleshooting section:

**Common issues:**
- Missing environment variables → Add in Railway dashboard
- Build failure → Check logs in Deployments tab
- App won't start → Review application logs
- Domain not resolving → Wait for DNS propagation (up to 24 hours)

All issues have solutions documented.

---

## 🔧 Configuration

### Q: Where do I put API keys and secrets?
**A:** Use environment variables in Railway:

1. Dashboard → Variables tab
2. Add each variable (STRIPE_SECRET_KEY, etc.)
3. Restart deployment
4. Variables never exposed in logs or UI

**Never commit secrets to GitHub!**

---

### Q: How many environment variables do I need?
**A:** About 50+, but only ~15 are essential for basic operation:

**Essential:**
- ENVIRONMENT, DEBUG
- BACKEND_URL, FRONTEND_URL, CORS_ORIGINS
- DATABASE_URL
- JWT_SECRET

**Integration Keys (add as needed):**
- Stripe: STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY
- Slack: SLACK_BOT_TOKEN, SLACK_WEBHOOK_URL
- Google: GOOGLE_SHEETS_CREDENTIALS, GOOGLE_SHEETS_SPREADSHEET_ID
- Shopify: SHOPIFY_API_KEY, SHOPIFY_API_PASSWORD

See `.env.production.example` for complete list.

---

### Q: Can I use SQLite in production?
**A:** **Not recommended:**
- ✅ Works for small deployments (<100 pilots)
- ❌ No horizontal scaling
- ❌ Poor concurrency
- ❌ Backup complexity

**Better:** Use PostgreSQL (Railway includes it, free tier available)

---

## 📊 Features & Usage

### Q: How many pilots can the system handle?
**A:** Depends on plan:

| Plan | Pilots | Concurrent Users | Database |
|------|--------|------------------|----------|
| Free | 2 | 10 | SQLite |
| Starter | 10 | 50 | SQLite/PostgreSQL |
| Pro | 50 | 100+ | PostgreSQL |
| Enterprise | 500+ | 1000+ | PostgreSQL + Scale |

Each plan auto-enforces limits via API.

---

### Q: What data should I export first?
**A:** Use the export feature to backup:

1. Dashboard → Export section
2. Select "Export All Pilots" → Excel
3. Select "Export All Actions" → CSV
4. Keep local copies for records

Data also stored in database backups.

---

### Q: How do I add pilots?
**A:** Three ways:

**1. Manual (Dashboard)**
- Add → Pilot Form → Save

**2. Bulk Import**
- Export template → Fill data → Import

**3. API**
- POST /api/pilot with JSON data
- See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

### Q: Can I customize the dashboard?
**A:** Currently limited customization:
- ✅ Dark mode toggle
- ✅ Column sorting/filtering
- ✅ Export column selection
- ❌ Custom layouts (future version)
- ❌ Custom reports (enterprise feature)

Contact support for custom development.

---

## 💰 Billing

### Q: How does the billing system work?
**A:** Stripe integration with 4 tiers:

- **Free**: $0, 2 pilots, basic analytics
- **Starter**: $49/mo, 10 pilots, advanced analytics
- **Professional**: $99/mo, 50 pilots, predictions + integrations
- **Enterprise**: $299/mo, 500+ pilots, custom features

Users upgrade/downgrade anytime with prorated charges.

---

### Q: How do I test billing without live Stripe keys?
**A:** Use Stripe test mode:

1. Get test keys from Stripe dashboard (sk_test_...)
2. Add to Railway variables (STRIPE_SECRET_KEY=sk_test_...)
3. Use test card numbers:
   - Success: 4242 4242 4242 4242
   - Fail: 4000 0000 0000 0002

No real charges in test mode.

---

### Q: What happens if a user's card declines?
**A:** Automated retry flow:

1. First decline: Retry in 3 days
2. Second decline: Email notification
3. Third decline: Subscription paused (no API access)
4. After 30 days: Subscription canceled

User can update card to resume access.

---

## 🔌 Integrations

### Q: How do I setup Slack integration?
**A:** 5 steps (10 minutes):

1. Create Slack App at api.slack.com
2. Copy Bot Token (xoxb-...)
3. Add to Railway: SLACK_BOT_TOKEN=xoxb-...
4. Set webhook channel in app config
5. Redeploy

Then use API: POST /api/integrations/slack/alert

See integration docs for examples.

---

### Q: Does Shopify auto-sync orders?
**A:** **Yes, real-time:**

1. Configure webhook in Shopify admin
2. Set URL: https://api.tryclariq.com/api/shopify/webhook/orders
3. Events: orders/create, orders/updated
4. Shopify sends updates automatically

Orders sync within 1-5 seconds.

---

### Q: How do I export to Google Sheets?
**A:** Two ways:

**1. One-time export**
- Dashboard → Export → Google Sheets button
- Authenticate with Google
- Data pushed to sheet

**2. Auto-sync (Premium)**
- Setup integration with service account
- Configure GOOGLE_SHEETS_SPREADSHEET_ID
- Auto-updates every hour

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for setup.

---

## 🚨 Monitoring & Troubleshooting

### Q: How do I know if the system is working?
**A:** Check health endpoint:

```bash
curl https://api.tryclariq.com/api/health
# Returns: {"status": "ok", "timestamp": "..."}
```

Also check:
- Dashboard loads without errors
- API endpoints responding (<1s response time)
- Database connectivity working
- Logs show no ERROR level messages

---

### Q: Why is the API slow?
**A:** Check in order:

1. **Database**: `curl https://api.tryclariq.com/api/performance/database`
   - Should be <50ms per query
   
2. **Network**: Check Railway metrics
   - CPU <80%? Memory <85%?
   - Network latency normal?

3. **Code**: Check application logs
   - Any N+1 queries?
   - Large data transfers?

4. **Solution**: Upgrade Railway plan or add database indices

---

### Q: How do I check logs?
**A:** Multiple options:

**Railway Dashboard:**
1. Deployments → Select deployment
2. Logs tab shows real-time output
3. Filter by ERROR to find issues

**Local Development:**
```bash
docker-compose logs -f backend
```

**Production Export:**
Get logs from Railway → Download as .csv

---

### Q: How do I backup the database?
**A:** Automatic & manual:

**Automatic (recommended):**
- Railway auto-backs up PostgreSQL daily
- 30-day retention (Professional+ plans)
- Restore in 1 click

**Manual:**
```bash
# SQLite
sqlite3 data/clariq_pilots.sqlite ".dump" > backup.sql

# PostgreSQL
pg_dump $DATABASE_URL > backup.sql

# Script
bash scripts/backup.sh
```

---

### Q: What if I lose all data?
**A:** Recovery options:

1. **Railway backups**: Restore from daily backup (1 click)
2. **Manual exports**: Use exported CSV files to reimport
3. **Rebuild**: Re-sync from Shopify (all order data)

Always maintain backups before going live!

---

## 🔐 Security

### Q: Is the platform secure?
**A:** Yes, enterprise-grade security:

✅ HTTPS/TLS encryption (Let's Encrypt)
✅ JWT authentication with signing
✅ SQL injection prevention
✅ CORS properly configured
✅ Rate limiting (100 req/s)
✅ Environment secrets management
✅ Password hashing (bcrypt)
✅ Security headers (HSTS, X-Frame-Options)

See README.md security section for details.

---

### Q: How do I secure API keys?
**A:** Best practices:

1. **Never** commit keys to GitHub
2. Use environment variables ONLY
3. Rotate keys regularly (Stripe, Shopify, etc)
4. Use different keys for dev/prod
5. Monitor API usage for anomalies
6. Revoke compromised keys immediately

---

### Q: Should I enable 2FA?
**A:** Yes, definitely:

1. Railway: Enable in account settings
2. GitHub: Enable for repository
3. Stripe: Enable for dashboard
4. Google: Enable for service account

This prevents unauthorized access.

---

## 📈 Performance & Scaling

### Q: What are the response time targets?
**A:** We aim for:

- **Pilot endpoints**: <100ms
- **Analytics endpoints**: <200ms
- **Export endpoints**: <500ms (file generation)
- **Health check**: <10ms

Check actual performance in Railway metrics.

---

### Q: How do I handle 1000+ pilots?
**A:** Scaling checklist:

1. Upgrade to PostgreSQL (not SQLite)
2. Add database indices (auto-added)
3. Enable query caching
4. Upgrade Railway to more resources
5. Consider CDN for static assets
6. Add Elasticsearch for search (optional)
7. Implement API pagination

Contact us for enterprise scaling strategy.

---

### Q: Can the system handle 100+ concurrent users?
**A:** Yes:

- ✅ FastAPI handles 1000s of concurrent requests
- ✅ Connection pooling configured
- ✅ Rate limiting prevents abuse
- ✅ Railway auto-scales CPU/memory

For 10000+ users, contact enterprise support.

---

## 🆘 Support & Help

### Q: How do I get help?
**A:** Multiple channels:

- **Docs**: [README.md](README.md), [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Deployment**: [PRODUCTION_LAUNCH.md](PRODUCTION_LAUNCH.md)
- **Troubleshooting**: Each guide has troubleshooting section
- **Email**: support@tryclariq.com
- **GitHub Issues**: Create issue in repository
- **Community**: Discord channel (link in README)

---

### Q: Is there a status page?
**A:** Yes! Check:

- **Railway Dashboard**: Real-time service status
- **Uptime Monitor**: status.tryclariq.com (optional)
- **GitHub Status**: github.com/Epunav1/clariq/issues

---

### Q: Can I request features?
**A:** Yes! Three ways:

1. **GitHub Issues**: For technical features
2. **Email**: Feature request to support@tryclariq.com
3. **Enterprise**: Custom features available

Most requested features prioritized for next release.

---

## 🔄 Maintenance & Updates

### Q: How often is the system updated?
**A:** Regular updates:

- **Critical security**: Immediate (within hours)
- **Bug fixes**: Weekly
- **Features**: Monthly
- **Major releases**: Quarterly

Updates are non-breaking and deployed automatically.

---

### Q: Will updates break my integration?
**A:** No, API is versioned:

- All changes are backward compatible
- Deprecations announced 6 months ahead
- Old API versions supported 1+ year
- Status page announces breaking changes

No action needed for most updates.

---

### Q: Can I rollback after an update?
**A:** Yes:

**Railway:** 
1. Deployments tab
2. Previous deployment → Redeploy
3. Takes ~2 minutes

**Docker:**
```bash
git checkout <previous-version>
docker-compose up -d
```

---

## 💡 Tips & Best Practices

### Q: What's the best way to onboard pilots?
**A:** Recommended sequence:

1. **Week 1**: Setup 5 test pilots
2. **Week 2**: Setup Shopify sync and verify data
3. **Week 3**: Setup integrations (Slack, email)
4. **Week 4**: Launch with first cohort (10 pilots)
5. **Week 5-6**: Gather feedback, iterate

See onboarding guide in docs.

---

### Q: How often should I check the dashboard?
**A:** Recommended:

- **Daily**: Review new orders and revenue
- **Weekly**: Analyze ROI trends, check alerts
- **Monthly**: Review pilot performance, plan adjustments
- **Quarterly**: Evaluate program ROI, scale/pause pilots

Alerts auto-notify major events.

---

### Q: What metrics matter most?
**A:** Key metrics to track:

1. **Total Revenue**: Overall program impact
2. **ROI %**: Is it profitable?
3. **Reorder Rate**: Customer satisfaction
4. **Profit Margin**: Unit economics
5. **Churn Risk**: Pilot continuation rate

Dashboard shows all of these automatically.

---

## 🎓 Learning Resources

### Q: Where do I learn how to use CLARIQ?
**A:** Resources available:

- **[README.md](README.md)**: Project overview
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)**: All endpoints
- **[PRODUCTION_LAUNCH.md](PRODUCTION_LAUNCH.md)**: Deployment guide
- **[DNS_SETUP.md](DNS_SETUP.md)**: Domain configuration
- **Video tutorials**: (coming soon)
- **Webinars**: Monthly (sign up in dashboard)

---

### Q: Are there code examples?
**A:** Yes, in API docs:

```python
# Python example
import requests

url = "https://api.tryclariq.com/api/pilot"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.get(url, headers=headers)
pilots = response.json()
```

```javascript
// JavaScript example
fetch('https://api.tryclariq.com/api/pilot', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
.then(r => r.json())
.then(pilots => console.log(pilots))
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for more examples.

---

## 🚀 Getting Started

**Not sure where to start?** Follow this order:

1. ✅ Read [README.md](README.md) (10 min)
2. ✅ Read [PRODUCTION_LAUNCH.md](PRODUCTION_LAUNCH.md) (15 min)
3. ✅ Setup Railway deployment (10 min)
4. ✅ Configure tryclariq.com domain (15 min)
5. ✅ Setup integrations (20 min)
6. ✅ Test with sample pilots (30 min)

**Total: ~1.5 hours to fully operational**

---

## ❓ Still Have Questions?

If your question isn't here:

1. **Check documentation**: Use Ctrl+F to search
2. **Review examples**: API_DOCUMENTATION.md has examples
3. **Check troubleshooting**: Each guide has troubleshooting section
4. **Email support**: support@tryclariq.com
5. **Create GitHub issue**: For bugs/features

---

**Last Updated:** July 9, 2024  
**Version:** CLARIQ 2.0.0

Questions? Check the guides above or contact support! 🚀
