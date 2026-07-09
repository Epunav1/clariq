# 🔐 Environment Variable Setup Guide

Complete reference for configuring CLARIQ production environment

---

## 📋 Quick Reference

**Total Variables Needed: 50+**

| Category | Required | Optional | Notes |
|----------|----------|----------|-------|
| Application | 5 | 0 | Must be set |
| Server | 2 | 0 | Must be set |
| Database | 1 | 0 | Must be set |
| Security | 2 | 0 | Must be set |
| Email (SMTP) | 5 | 0 | Required for feedback |
| Integrations | 12 | ✓ | Set only if using |
| Monitoring | 3 | ✓ | Optional but recommended |

---

## ✅ Application Configuration

### `ENVIRONMENT`
```
Value: production
Purpose: Sets Flask/FastAPI to production mode (no debug, optimized)
Impact: High - affects security and performance
Example: ENVIRONMENT=production
```

### `DEBUG`
```
Value: false
Purpose: Disables debug mode (no verbose errors shown to users)
Impact: Critical for security
Example: DEBUG=false
Note: NEVER use true in production
```

### `LOG_LEVEL`
```
Value: INFO (or WARNING for less logging)
Purpose: Controls verbosity of application logs
Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
Impact: Medium - affects log size and performance
Example: LOG_LEVEL=INFO
```

### `SECRET_KEY` (FastAPI only)
```
Value: Random 32+ character string
Purpose: Session encryption and CSRF token generation
Impact: Critical for security
Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
Example: SECRET_KEY=AZ_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
```

### `APP_NAME`
```
Value: CLARIQ
Purpose: Display name in logs and UI
Impact: Low - cosmetic
Example: APP_NAME=CLARIQ
```

---

## 🌐 Server Configuration

### `BACKEND_URL`
```
Value: https://api.tryclariq.com
Purpose: Absolute URL where backend API is accessible
Impact: High - used in CORS, emails, redirects
Example: BACKEND_URL=https://api.tryclariq.com
Format: Must be HTTPS in production
Note: No trailing slash
```

### `FRONTEND_URL`
```
Value: https://tryclariq.com
Purpose: Absolute URL where frontend dashboard is accessible
Impact: High - used in CORS, OAuth redirects, emails
Example: FRONTEND_URL=https://tryclariq.com
Format: Must be HTTPS in production
Note: No trailing slash
```

### `CORS_ORIGINS` (Optional - auto-derived from above)
```
Value: https://tryclariq.com,https://www.tryclariq.com,https://api.tryclariq.com
Purpose: Allowed domains for cross-origin requests
Impact: High - blocks requests from other domains
Format: Comma-separated URLs
Example: CORS_ORIGINS=https://tryclariq.com,https://www.tryclariq.com
Note: Include www and api subdomains if used
```

---

## 💾 Database Configuration

### `DATABASE_URL`
```
SQLite (Development/Small):
  DATABASE_URL=sqlite:///./data/clariq.db
  
PostgreSQL (Production/Recommended):
  DATABASE_URL=postgresql://user:password@host:5432/clariq
  
SQLite with full path:
  DATABASE_URL=sqlite:////Users/ebubeepuna/Downloads/clariq/data/clariq.db

Purpose: Database connection string
Impact: Critical - app doesn't run without this
Options: SQLite (simple), PostgreSQL (scalable)
Note: PostgreSQL recommended for production
```

### `DATABASE_URL` Examples

**Railway PostgreSQL:**
```
DATABASE_URL=postgresql://postgres:abc123@postgres.railway.internal:5432/clariq
(Automatically provided by Railway if you add PostgreSQL service)
```

**Local SQLite:**
```
DATABASE_URL=sqlite:///./data/clariq.db
(Creates database in data/ folder)
```

**Absolute SQLite Path:**
```
DATABASE_URL=sqlite:////Users/ebubeepuna/Downloads/clariq/data/clariq.db
```

---

## 🔐 Security Configuration

### `JWT_SECRET`
```
Value: Random 32+ character cryptographically secure string
Purpose: Sign and verify JWT authentication tokens
Impact: Critical - all user authentication depends on this
Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
Example: AZ_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
Length: Minimum 32 characters
Note: NEVER share or expose this value
```

### `JWT_ALGORITHM`
```
Value: HS256
Purpose: Algorithm for signing JWT tokens
Options: HS256, RS256 (HS256 for most cases)
Example: JWT_ALGORITHM=HS256
```

### `JWT_EXPIRATION_HOURS`
```
Value: 720 (30 days)
Purpose: How long before token expires and user must login again
Impact: Security vs. convenience tradeoff
Options: 24 (1 day), 168 (1 week), 720 (30 days)
Example: JWT_EXPIRATION_HOURS=720
```

---

## 📧 Email Configuration (SMTP)

**Required for:** Feedback system, notifications, confirmations

### Gmail Setup (Free, Recommended)

```bash
# Step 1: Enable 2-Factor Authentication
# https://myaccount.google.com/security

# Step 2: Create App Password
# https://myaccount.google.com/apppasswords
# Select: Mail
# Select: Windows (or other)
# Copy: 16-character password

# Step 3: Add to environment
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<16-char-app-password-from-step-2>
SMTP_FROM=noreply@tryclariq.com
OWNER_EMAIL=your-email@gmail.com
```

### SendGrid Setup (Paid, More Reliable)

```bash
# Step 1: Create SendGrid account
# https://sendgrid.com

# Step 2: Create API key
# Go to: Settings → API Keys → Create API Key

# Step 3: Add to environment
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxxxxxxxxxxxx (your API key)
SMTP_FROM=noreply@tryclariq.com
OWNER_EMAIL=your-email@gmail.com
```

### Mailgun Setup (Pay-as-you-go)

```bash
# Step 1: Create Mailgun account
# https://mailgun.com

# Step 2: Get SMTP credentials
# Domain settings → SMTP credentials

# Step 3: Add to environment
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@yourdomain.mailgun.org
SMTP_PASSWORD=<mailgun-password>
SMTP_FROM=noreply@tryclariq.com
OWNER_EMAIL=your-email@gmail.com
```

### SMTP Environment Variables

#### `SMTP_HOST`
```
Purpose: SMTP server hostname
Gmail: smtp.gmail.com
SendGrid: smtp.sendgrid.net
Mailgun: smtp.mailgun.org
Example: SMTP_HOST=smtp.gmail.com
```

#### `SMTP_PORT`
```
Purpose: SMTP server port
Standard TLS: 587 (most common)
SSL: 465
Standard (no TLS): 25
Example: SMTP_PORT=587
Note: 587 recommended
```

#### `SMTP_USER`
```
Purpose: Username for SMTP authentication
Gmail: your-email@gmail.com
SendGrid: apikey
Mailgun: postmaster@yourdomain.mailgun.org
Example: SMTP_USER=your-email@gmail.com
```

#### `SMTP_PASSWORD`
```
Purpose: Password for SMTP authentication
Gmail: 16-character app password (NOT your regular password)
SendGrid: Your API key
Mailgun: Your Mailgun password
Example: SMTP_PASSWORD=abcd efgh ijkl mnop
Note: For Gmail, MUST use app password, not regular password
```

#### `SMTP_FROM`
```
Purpose: "From" address in sent emails
Format: email@domain.com or Name <email@domain.com>
Example: SMTP_FROM=noreply@tryclariq.com
Example: SMTP_FROM=CLARIQ <noreply@tryclariq.com>
Note: Domain should match your sending service domain
```

#### `OWNER_EMAIL`
```
Purpose: Email address where you receive feedback notifications
Format: your-actual-email@gmail.com
Example: OWNER_EMAIL=user@gmail.com
Note: This is YOUR email - where notifications go
```

---

## 💳 Stripe Configuration (Optional)

**Required for:** Billing and payments

### Test Mode (Development)

```
# Create account: https://stripe.com
# Go to: Developers → API Keys
# Copy Test Keys:

STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxx
STRIPE_ENVIRONMENT=test
```

### Production Mode (Live)

```
# Switch to Live Mode in Stripe Dashboard
# Copy Live Keys:

STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxxxxxxxxx
STRIPE_ENVIRONMENT=production

WARNING: Never test with live mode keys!
         Always test with test mode first.
```

### Stripe Variables

#### `STRIPE_SECRET_KEY`
```
Value: sk_test_... or sk_live_...
Purpose: Secret key for server-side Stripe operations
Impact: Critical - never expose or share
Security: Treat like a password
Example: STRIPE_SECRET_KEY=sk_test_51abc123XYZ
```

#### `STRIPE_PUBLISHABLE_KEY`
```
Value: pk_test_... or pk_live_...
Purpose: Public key for client-side operations (safe to expose)
Impact: Medium - identifies your Stripe account
Example: STRIPE_PUBLISHABLE_KEY=pk_test_51abc123XYZ
```

#### `STRIPE_WEBHOOK_SECRET`
```
Value: whsec_... (from Webhook settings)
Purpose: Verify webhook requests are from Stripe
Impact: High - security critical
Setup: Developers → Webhooks → Add endpoint
Example: STRIPE_WEBHOOK_SECRET=whsec_abc123xyz
```

---

## 🤖 Slack Configuration (Optional)

**Required for:** Slack notifications and alerts

### Setup

```bash
# Step 1: Go to https://api.slack.com/apps
# Step 2: Create New App → From scratch
# Step 3: App Name: CLARIQ Bot
# Step 4: Select your workspace
# Step 5: Go to OAuth & Permissions
# Step 6: Add Scopes:
#   - chat:write
#   - commands
# Step 7: Install to Workspace
# Step 8: Copy Bot User OAuth Token: xoxb-...
# Step 9: Add to environment
```

#### `SLACK_BOT_TOKEN`
```
Value: xoxb-xxxxxxxxxxxx-xxxxxxxxxxxxxx-xxxxxxxxxxxx
Purpose: Authentication for Slack bot
Impact: High - bot won't work without this
Setup: https://api.slack.com/apps → OAuth & Permissions → Copy Bot Token
Example: SLACK_BOT_TOKEN=xoxb-12345-67890-abcdefg
```

#### `SLACK_WEBHOOK_URL` (Alternative)
```
Value: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
Purpose: Send messages to Slack without bot (simpler)
Impact: Medium - less flexible than bot token
Setup: https://api.slack.com/apps → Incoming Webhooks → Add New Webhook
Example: SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

#### `SLACK_CHANNEL`
```
Value: #alerts (or #channel-name)
Purpose: Default channel for alerts
Impact: Low - can override per message
Example: SLACK_CHANNEL=#alerts
```

---

## 📊 Google Sheets Configuration (Optional)

**Required for:** Google Sheets export and sync

### Setup

```bash
# Step 1: Go to https://console.cloud.google.com
# Step 2: Create new project: CLARIQ
# Step 3: Enable APIs:
#   - Google Sheets API
#   - Google Drive API
# Step 4: Service Accounts:
#   - Create service account
#   - Create JSON key
#   - Download JSON file
# Step 5: Add to environment
```

#### `GOOGLE_SHEETS_CREDENTIALS`
```
Value: {entire JSON credentials file as string}
Purpose: Authentication for Google Sheets access
Format: JSON object, single line or base64 encoded
Example:
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account","project_id":"clariq","private_key":"-----BEGIN PRIVATE KEY-----...-----END PRIVATE KEY-----\n"}

Setup:
1. Download JSON from Google Cloud Console
2. Copy entire contents
3. Replace newlines with \n
4. Add as single environment variable
```

#### `GOOGLE_SHEETS_SPREADSHEET_ID`
```
Value: 1a2b3c4d5e6f7g8h9i0j (from URL)
Purpose: ID of spreadsheet to export to
Format: Long alphanumeric string
Find in: Google Sheets URL: /spreadsheets/d/[ID_HERE]/edit
Example: GOOGLE_SHEETS_SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0j1k2l3m
```

---

## 🛒 Shopify Configuration (Optional)

**Required for:** Shopify webhook integration

#### `SHOPIFY_API_KEY`
```
Value: Your Shopify API key
Purpose: Authenticate with Shopify API
Setup: Shopify Admin → Apps and integrations → Develop apps
Example: SHOPIFY_API_KEY=1234567890abcdef1234567890abcdef
```

#### `SHOPIFY_API_SECRET`
```
Value: Your Shopify API secret
Purpose: Verify webhook authenticity
Setup: Shopify Admin → Webhooks → Signing secret
Example: SHOPIFY_API_SECRET=whsec_abc123xyz
```

#### `SHOPIFY_WEBHOOK_SECRET`
```
Value: Same as API_SECRET
Purpose: Verify incoming webhooks are from Shopify
Impact: Critical for security
Example: SHOPIFY_WEBHOOK_SECRET=whsec_abc123xyz
```

---

## 📈 Monitoring Configuration (Optional)

### `SENTRY_DSN` (Error Tracking)
```
Value: https://key@sentry.io/project-id
Purpose: Send errors to Sentry for monitoring
Setup: https://sentry.io → Create project
Example: SENTRY_DSN=https://abc123def456@sentry.io/1234567
Impact: Low - optional but recommended
```

### `LOG_RETENTION_DAYS`
```
Value: 30 (days to keep logs)
Purpose: Automatic log cleanup
Options: 7, 14, 30, 90
Example: LOG_RETENTION_DAYS=30
```

---

## 📝 Configuration Checklist

### ✅ Minimum Required (to go live)

```
[ ] ENVIRONMENT=production
[ ] DEBUG=false
[ ] BACKEND_URL=https://api.tryclariq.com
[ ] FRONTEND_URL=https://tryclariq.com
[ ] DATABASE_URL=sqlite or postgresql
[ ] JWT_SECRET=<generated>
[ ] SMTP_HOST=smtp.gmail.com (or your provider)
[ ] SMTP_PORT=587
[ ] SMTP_USER=your-email@gmail.com
[ ] SMTP_PASSWORD=<app-password>
[ ] OWNER_EMAIL=your-email@gmail.com
```

### ✅ Highly Recommended

```
[ ] CORS_ORIGINS=https://tryclariq.com,https://www.tryclariq.com
[ ] LOG_LEVEL=INFO
[ ] STRIPE_SECRET_KEY=sk_test_... (if using billing)
[ ] STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### ✅ Nice to Have (Optional)

```
[ ] SLACK_BOT_TOKEN=xoxb-... (if using Slack)
[ ] SENTRY_DSN=... (if monitoring)
[ ] GOOGLE_SHEETS_CREDENTIALS=... (if exporting)
```

---

## 🚀 Setting Variables in Railway

### Step 1: Go to Railway Dashboard
```
1. Project → Variables tab
2. Click "Add Variable"
```

### Step 2: Add Each Variable
```
Name: ENVIRONMENT
Value: production

Name: DEBUG
Value: false

(Continue for each variable)
```

### Step 3: Save & Redeploy
```
- Railway auto-saves
- Railway auto-redeploys (2-5 minutes)
- Check logs for "Application startup complete"
```

---

## ✅ Verification

**After setting all variables:**

```bash
# Test health endpoint
curl https://api.tryclariq.com/api/health
# Expected: {"status": "ok"}

# Test support status (shows if email configured)
curl https://api.tryclariq.com/api/support/status
# Expected: {"status": "operational", "email_service": "configured"}

# Test feedback submission
curl -X POST https://api.tryclariq.com/api/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "test@example.com",
    "subject": "Test",
    "message": "Testing configuration"
  }'
# Expected: {"feedback_id": 1, "status": "received"}
```

---

## 🆘 Troubleshooting

### "Application won't start"
- Check LOG_LEVEL is set correctly
- Verify DATABASE_URL is valid format
- Ensure JWT_SECRET is set
- Check Railway logs for specific error

### "Emails not sending"
- Verify SMTP credentials exact
- For Gmail: MUST use app password, not regular password
- Check OWNER_EMAIL is valid
- Verify SMTP_FROM is set
- Check Railway logs for SMTP errors

### "CORS errors in dashboard"
- Verify CORS_ORIGINS includes your domain
- Include both www and non-www versions
- Ensure HTTPS is used (not HTTP)
- Redeploy after changing CORS_ORIGINS

### "API returns 401 (Unauthorized)"
- Check JWT_SECRET is set
- Verify token format in Authorization header
- Ensure JWT_ALGORITHM matches token algorithm

---

## 📋 Complete .env.production Template

Copy and customize:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
APP_NAME=CLARIQ

# Server
BACKEND_URL=https://api.tryclariq.com
FRONTEND_URL=https://tryclariq.com
CORS_ORIGINS=https://tryclariq.com,https://www.tryclariq.com

# Database
DATABASE_URL=sqlite:///./data/clariq.db

# Security
JWT_SECRET=<generate-with-python>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=720

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@tryclariq.com
OWNER_EMAIL=your-email@gmail.com

# Stripe (Optional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Slack (Optional)
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL=#alerts

# Google Sheets (Optional)
GOOGLE_SHEETS_CREDENTIALS={...}
GOOGLE_SHEETS_SPREADSHEET_ID=...

# Shopify (Optional)
SHOPIFY_WEBHOOK_SECRET=...

# Monitoring (Optional)
SENTRY_DSN=https://...
LOG_RETENTION_DAYS=30
```

---

**All set! You're ready to launch.** 🚀
