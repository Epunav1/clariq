# CLARIQ Domain Setup Guide

Configure tryclariq.com to point to your production infrastructure.

---

## 📋 Quick Overview

| Domain | Purpose | Points To |
|--------|---------|-----------|
| `tryclariq.com` | Main dashboard & API | Load Balancer / Nginx |
| `www.tryclariq.com` | www redirect | Nginx / Load Balancer |
| `api.tryclariq.com` | API subdomain | Backend Service |

---

## 🔧 DNS Configuration

### Step 1: Get Your Infrastructure Details

**For Railway:**
```bash
# After deployment, get the public URL
railway open dashboard
# Copy the assigned domain: something-production.railway.app
```

**For AWS / DigitalOcean / Self-Hosted:**
```bash
# Get your public IP or load balancer DNS
dig your-server.com +short
# Returns: your.public.ip.address
```

### Step 2: Update DNS Records

Go to your domain registrar (GoDaddy, Namecheap, Route53, etc) and add:

#### A. Main Domain
```
Type:    A (or CNAME)
Name:    tryclariq.com (or @)
Value:   your.public.ip.or.lb.dns
TTL:     300 (or 3600)
```

#### B. WWW Subdomain
```
Type:    CNAME
Name:    www
Value:   tryclariq.com
TTL:     300 (or 3600)
```

#### C. API Subdomain
```
Type:    CNAME (or A)
Name:    api
Value:   tryclariq.com (or your.public.ip)
TTL:     300 (or 3600)
```

#### D. Mail Records (Optional)
```
Type:    MX
Name:    tryclariq.com
Value:   mail.tryclariq.com
Priority: 10
TTL:     3600
```

---

## 🌐 DNS Propagation

After updating DNS records:

```bash
# Wait 15-30 minutes for propagation
# Then verify:

# Check A record
dig tryclariq.com +short

# Check CNAME records
dig www.tryclariq.com +short
dig api.tryclariq.com +short

# Full DNS check
nslookup tryclariq.com

# Trace DNS resolution
dig tryclariq.com +trace
```

**Expected output:**
```
tryclariq.com.  3600  IN  A  your.public.ip.address
www.tryclariq.com. 3600 IN  CNAME  tryclariq.com.
api.tryclariq.com. 3600 IN  CNAME  tryclariq.com.
```

---

## 🔐 SSL/TLS Certificate Setup

### Option 1: Let's Encrypt (Free, Automated)

**On Railway:**
```
✅ Automatic - Railway handles SSL/TLS
```

**On AWS/DigitalOcean/Self-Hosted:**
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --nginx -d tryclariq.com -d www.tryclariq.com -d api.tryclariq.com

# Auto-renew (runs daily)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Verify renewal
sudo certbot renew --dry-run
```

**Nginx configuration:**
```nginx
# In /etc/nginx/sites-available/tryclariq.com

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name tryclariq.com www.tryclariq.com api.tryclariq.com;
    return 301 https://$host$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name tryclariq.com www.tryclariq.com api.tryclariq.com;

    # Certbot paths
    ssl_certificate /etc/letsencrypt/live/tryclariq.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tryclariq.com/privkey.pem;

    # Enable HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

### Option 2: AWS Certificate Manager (Free)

```bash
# In AWS Console:
# 1. Go to Certificate Manager
# 2. Request certificate
# 3. Add domains:
#    - tryclariq.com
#    - *.tryclariq.com (wildcard)
# 4. Choose DNS validation
# 5. Add CNAME records AWS provides
# 6. Attach to ALB/CloudFront
```

### Option 3: CloudFlare

```bash
# 1. Add site to Cloudflare
# 2. Update nameservers at registrar
# 3. Cloudflare > SSL/TLS > Overview
# 4. Choose: Flexible, Full, or Full (Strict)
# 5. Enable auto-renew
```

---

## ✅ Verification Checklist

```bash
# 1. DNS resolves
dig tryclariq.com +short
# Should return your IP or load balancer DNS

# 2. HTTP works
curl -I http://tryclariq.com
# Should redirect to HTTPS

# 3. HTTPS works
curl -I https://tryclariq.com
# Should show 200/301 with SSL headers

# 4. Certificate is valid
curl -v https://tryclariq.com
# Should show: "Verifying OK" or similar

# 5. All subdomains work
curl -I https://www.tryclariq.com
curl -I https://api.tryclariq.com

# 6. HSTS header present
curl -I https://tryclariq.com | grep Strict-Transport-Security
# Should show: max-age=31536000

# 7. Dashboard loads
open https://tryclariq.com
# Should see CLARIQ dashboard

# 8. API works
curl https://api.tryclariq.com/api/health
# Should return: {"status": "ok"}
```

---

## 🚨 Troubleshooting

### DNS not resolving
```bash
# Clear cache (macOS)
sudo dscacheutil -flushcache

# Clear cache (Linux)
sudo systemctl restart systemd-resolved

# Check with public resolver
dig tryclariq.com @8.8.8.8
```

### SSL certificate errors
```bash
# Check cert details
openssl s_client -connect tryclariq.com:443

# Check cert expiration
echo | openssl s_client -servername tryclariq.com -connect tryclariq.com:443 2>/dev/null | openssl x509 -noout -dates

# Renew Let's Encrypt
sudo certbot renew --force-renewal
```

### 404 errors after DNS setup
```bash
# Check nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Check logs
sudo tail -f /var/log/nginx/error.log
```

### Slow resolution
```bash
# Use faster nameservers
# In /etc/resolv.conf or system settings:
nameserver 8.8.8.8           # Google
nameserver 1.1.1.1           # Cloudflare
```

---

## 🔄 Update Application Configuration

After DNS is working, update your application:

### Backend (.env.production)
```bash
BACKEND_URL=https://api.tryclariq.com
FRONTEND_URL=https://tryclariq.com
CORS_ORIGINS=https://tryclariq.com,https://www.tryclariq.com,https://api.tryclariq.com
```

### Integrations

**Stripe:**
- Update redirect URLs to `https://tryclariq.com/billing`
- Update webhook endpoint to `https://api.tryclariq.com/api/webhooks/stripe`

**Shopify:**
- Update webhook URLs to `https://api.tryclariq.com/api/shopify/webhook/*`

**Slack:**
- Update redirect URL to `https://api.tryclariq.com/api/integrations/slack/callback`

**Google Sheets:**
- Update OAuth redirect to `https://api.tryclariq.com/api/integrations/sheets/callback`

---

## 📊 Domain Configuration Summary

```
tryclariq.com
├─ Frontend Dashboard
│  └─ CORS: https://tryclariq.com
│  └─ Redirect: http → https
│
├─ API Backend (api.tryclariq.com)
│  ├─ Health: /api/health
│  ├─ Webhooks: /api/webhooks/*
│  └─ CORS: https://api.tryclariq.com
│
├─ SSL/TLS Certificate
│  ├─ Provider: Let's Encrypt (or AWS/Cloudflare)
│  ├─ Auto-renew: Enabled
│  └─ Subdomains: tryclariq.com, www, api
│
└─ DNS Records
   ├─ A: tryclariq.com → IP/LB
   ├─ CNAME: www → tryclariq.com
   └─ CNAME: api → tryclariq.com
```

---

## 🎯 Next Steps

1. ✅ Update DNS records (5 min)
2. ✅ Wait for propagation (15-30 min)
3. ✅ Setup SSL certificate (5-10 min)
4. ✅ Update .env.production (2 min)
5. ✅ Restart services (1 min)
6. ✅ Verify all endpoints (5 min)

**Total time:** 30-50 minutes

---

**For issues, see DEPLOYMENT.md troubleshooting section or check Nginx logs:**

```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```
