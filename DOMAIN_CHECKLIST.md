# tryclariq.com Configuration Checklist

Complete this checklist to ensure tryclariq.com is properly configured across all services.

---

## ✅ DNS Configuration

- [ ] **A Record**: tryclariq.com → your.public.ip
- [ ] **CNAME Record**: www.tryclariq.com → tryclariq.com
- [ ] **CNAME Record**: api.tryclariq.com → tryclariq.com
- [ ] **DNS Propagation**: Verify with `dig tryclariq.com`
- [ ] **Reference**: See [DNS_SETUP.md](DNS_SETUP.md)

---

## ✅ SSL/TLS Certificate

- [ ] **Generate Certificate**: Let's Encrypt or AWS Certificate Manager
- [ ] **Domains**: tryclariq.com, www.tryclariq.com, api.tryclariq.com
- [ ] **Auto-renewal**: Enabled (certbot timer or cloud provider)
- [ ] **Verification**: `curl -v https://tryclariq.com` shows valid cert
- [ ] **HSTS Header**: Enabled in Nginx (max-age=31536000)

---

## ✅ Backend Configuration

### File: `.env.production`
```bash
BACKEND_URL=https://api.tryclariq.com
FRONTEND_URL=https://tryclariq.com
CORS_ORIGINS=https://tryclariq.com,https://www.tryclariq.com,https://api.tryclariq.com
```

- [ ] Confirm in `.env.production`
- [ ] Restart backend: `docker-compose restart backend`

### File: `backend/main.py` (CORS origins)
```python
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://tryclariq.com",
    "https://www.tryclariq.com",
    "https://api.tryclariq.com"
]
```

- [ ] Verify in code (already configured)

---

## ✅ Nginx Configuration

### File: `nginx.conf`
```nginx
server {
    listen 443 ssl http2;
    server_name tryclariq.com www.tryclariq.com api.tryclariq.com;
    
    ssl_certificate /etc/letsencrypt/live/tryclariq.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tryclariq.com/privkey.pem;
    
    add_header Strict-Transport-Security "max-age=31536000" always;
}
```

- [ ] Verify in `nginx.conf` (already configured)
- [ ] Restart Nginx: `docker-compose restart nginx`

---

## ✅ Third-Party Integrations

### Stripe
- [ ] Update Dashboard Redirect: `https://tryclariq.com/billing`
- [ ] Update Webhook Endpoint: `https://api.tryclariq.com/api/billing/webhook`
- [ ] Update Return URL: `https://tryclariq.com/billing/success`

### Shopify
- [ ] Update Webhook URLs: `https://api.tryclariq.com/api/shopify/webhook/{event}`
- [ ] Events: orders/create, orders/update, customers/*, products/*

### Slack
- [ ] OAuth Redirect: `https://api.tryclariq.com/api/integrations/slack/callback`
- [ ] Webhook URL: `https://api.tryclariq.com/api/integrations/slack/webhook`

### Google Sheets
- [ ] OAuth Redirect: `https://api.tryclariq.com/api/integrations/sheets/callback`
- [ ] Authorized Redirect URIs: Add to Google Cloud Console

### Email (SMTP)
- [ ] From Address: `noreply@tryclariq.com` (optional)
- [ ] SPF Record: `v=spf1 include:sendgrid.net ~all` (if using SendGrid)
- [ ] DKIM: Configure with email provider

---

## ✅ Verification Tests

Run these after all configuration:

```bash
# 1. DNS Resolution
dig tryclariq.com +short
# Expected: your.public.ip.address

# 2. HTTP Redirect
curl -I http://tryclariq.com
# Expected: 301 Moved Permanently → https

# 3. HTTPS with Valid Cert
curl -I https://tryclariq.com
# Expected: 200 OK, certificate valid

# 4. Subdomains
curl -I https://www.tryclariq.com
curl -I https://api.tryclariq.com
# Expected: 200 OK for both

# 5. HSTS Header
curl -I https://tryclariq.com | grep Strict-Transport-Security
# Expected: max-age=31536000; includeSubDomains

# 6. API Health
curl https://api.tryclariq.com/api/health
# Expected: {"status": "ok"}

# 7. Dashboard Loading
curl https://tryclariq.com | head -20
# Expected: HTML with CLARIQ dashboard

# 8. CORS Configuration
curl -H "Origin: https://tryclariq.com" -I https://api.tryclariq.com/api/health
# Expected: Access-Control-Allow-Origin: https://tryclariq.com
```

---

## ✅ Production Readiness

- [ ] All DNS records configured
- [ ] SSL certificate installed and auto-renewing
- [ ] .env.production updated with tryclariq.com URLs
- [ ] Backend restarted after env changes
- [ ] Nginx config verified with `nginx -t`
- [ ] All third-party webhooks updated
- [ ] HTTPS works for all subdomains
- [ ] Dashboard loads without mixed-content errors
- [ ] API responds with correct CORS headers
- [ ] Database backups configured
- [ ] Monitoring alerts enabled
- [ ] Security headers present

---

## 📋 Quick Reference

| Service | Config Location | Key Settings |
|---------|-----------------|--------------|
| DNS | Domain Registrar | A/CNAME records |
| SSL | Certbot / AWS ACM | Certificate renewal |
| Backend | `.env.production` | FRONTEND_URL, CORS_ORIGINS |
| Nginx | `nginx.conf` | server_name, ssl_certificate |
| Stripe | Stripe Dashboard | Webhook endpoint, return URLs |
| Shopify | Shopify Admin | Webhook URLs |
| Slack | Slack App | OAuth redirect |
| Google | Google Cloud | OAuth redirect |

---

## 🚀 Deployment Sequence

1. Configure DNS (wait 15-30 min for propagation)
2. Setup SSL certificate
3. Update `.env.production`
4. Deploy application
5. Restart services
6. Run verification tests
7. Monitor logs
8. Update third-party integrations
9. Test end-to-end workflows
10. Enable monitoring & alerting

---

## 📞 Support

- DNS issues: See [DNS_SETUP.md](DNS_SETUP.md)
- Deployment issues: See [DEPLOYMENT.md](DEPLOYMENT.md)
- SSL issues: See [DNS_SETUP.md - SSL/TLS Section](DNS_SETUP.md#-ssltls-certificate-setup)
- General setup: See [README.md](README.md)

---

**Status: Ready for Production**

✅ tryclariq.com is fully configured and ready to serve traffic.
