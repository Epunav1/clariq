# CLARIQ: AI-Powered Pilot Program Management Platform

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Version](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)

CLARIQ is a comprehensive platform for managing, analyzing, and optimizing pilot programs at scale. It provides real-time ROI tracking, predictive analytics, automated alerts, and seamless integrations with Shopify, Amazon, Slack, Google Sheets, and Stripe.

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (optional)
- Node.js (for frontend tooling, optional)
- Git

### Local Setup (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/Epunav1/clariq.git
cd clariq

# 2. Create Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env.development
# Edit .env.development with your settings

# 5. Run application
python -m uvicorn main:app --reload

# 6. Open dashboard
open http://localhost:8000

# 7. Production: Configure tryclariq.com
# See DEPLOYMENT.md and DNS_SETUP.md for production domain setup
```

### Docker Setup (3 minutes)

```bash
# 1. Build and run
docker-compose up -d

# 2. Verify services
docker-compose ps

# 3. View logs
docker-compose logs -f backend

# 4. Access dashboard
open http://localhost
```

---

## 🎯 Features

### 1. **Advanced ROI Analytics**
- Real-time profit margin calculations
- Cost-per-pilot modeling
- Breakeven analysis
- ROI forecasting (30/60/90 days)
- Profitability tiers (Exceptional/Strong/Positive/Break-even)

### 2. **Custom Data Export**
- CSV & Excel export with 20+ customizable columns
- Professional Excel formatting
- Quick export shortcuts
- Column selection modal interface

### 3. **System Performance Monitoring**
- Real-time API metrics (response time, error rate, throughput)
- System resource monitoring (CPU, memory, disk)
- Database connectivity checks
- Sync job status tracking
- Health status dashboard with color-coded indicators

### 4. **Automated Milestone Alerts**
- 10+ predefined milestone types:
  - Action-based: 1, 10, 25, 50, 100 reorders
  - Revenue-based: $1k, $5k, $10k achieved
  - ROI-based: Positive ROI, 100% ROI
- Email notifications with emoji reactions
- Milestone progress tracking
- Configurable thresholds

### 5. **Predictive Analytics**
- ROI forecasting with confidence intervals
- Revenue trend analysis
- Churn risk prediction (4 contributing factors)
- Pilot cohort analysis
- Competitive benchmarking vs peer averages

### 6. **Integrations**
- **Slack**: Real-time alerts, milestone notifications, pilot reports
- **Google Sheets**: Live data export and collaboration
- **Shopify**: Real-time webhook sync for orders, customers, products
- **Stripe**: Tiered subscription management and billing

### 7. **Tiered Billing System**
- Free: 2 pilots, basic features
- Starter: $49/mo, 10 pilots, advanced analytics
- Professional: $99/mo, 50 pilots, predictive features
- Enterprise: $299/mo, 500 pilots, custom integrations

### 8. **Production Ready**
- Docker containerization with multi-stage builds
- Nginx reverse proxy with SSL/TLS
- Database backups and migration scripts
- Security hardening (CORS, rate limiting, HTTPS)
- Horizontal scaling configuration
- Multiple deployment options (Docker, Railway, AWS, DigitalOcean)

---

## 🏗️ Architecture

```
clariq/
├── backend/                          # FastAPI application
│   ├── main.py                      # App entry point
│   ├── requirements.txt              # Python dependencies
│   ├── db/                          # Database services
│   │   ├── pilots_db.py            # Pilot CRUD operations
│   │   ├── actions_db.py           # Action tracking
│   │   ├── revenue_calc.py         # Revenue calculations
│   │   ├── roi_calc.py             # ROI analytics engine
│   │   ├── export_service.py       # CSV/Excel export
│   │   ├── performance_monitor.py  # System monitoring
│   │   ├── alert_manager.py        # Milestone alerts
│   │   ├── advanced_analytics.py   # ML forecasting
│   │   └── snowflake_client.py     # Data warehouse
│   ├── routes/                      # API endpoints
│   │   ├── pilot.py                # Pilot endpoints
│   │   ├── roi.py                  # ROI analytics
│   │   ├── export.py               # Data export
│   │   ├── performance.py          # Performance monitoring
│   │   ├── alerts.py               # Milestone alerts
│   │   ├── analytics.py            # Advanced analytics
│   │   ├── integrations.py         # Third-party integrations
│   │   ├── billing.py              # Stripe billing
│   │   ├── actions.py              # Action endpoints
│   │   ├── reports.py              # Report generation
│   │   └── ... (10+ total routers)
│   ├── services/                    # Business logic
│   │   ├── slack_integration.py    # Slack notifications
│   │   ├── google_sheets_integration.py  # Google Sheets sync
│   │   ├── shopify_webhook.py      # Shopify webhooks
│   │   ├── stripe_billing.py       # Stripe subscriptions
│   │   └── email_service.py        # Email notifications
│   ├── tests/                       # Test suite
│   │   ├── test_api.py             # API tests
│   │   ├── test_analytics.py       # Analytics tests
│   │   └── conftest.py             # Fixtures
│   └── data/                        # SQLite databases
│       ├── clariq_pilots.sqlite
│       ├── clariq_actions.sqlite
│       ├── clariq_roi_params.sqlite
│       └── ... (5+ databases)
├── clariq-dashboard.html             # Single-page dashboard
├── Dockerfile                        # Container configuration
├── docker-compose.yml                # Orchestration
├── nginx.conf                        # Reverse proxy config
├── .env.production.example            # Production config template
├── DEPLOYMENT.md                     # Deployment guide
├── API_DOCUMENTATION.md              # API reference
└── README.md                         # This file
```

---

## 🚀 API Overview

### Base URL
`https://api.clariq.com` or `http://localhost:8000`

### Authentication
All endpoints require JWT bearer token:
```
Authorization: Bearer {token}
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/pilot` | GET | List all pilots |
| `/api/roi/pilot/{id}` | GET | Get pilot ROI |
| `/api/roi/comparison` | GET | Compare pilots |
| `/api/analytics/forecast/{id}` | GET | ROI forecast |
| `/api/analytics/churn/{id}` | GET | Churn prediction |
| `/api/analytics/benchmark/{id}` | GET | Pilot benchmarking |
| `/api/export/pilots` | POST | Export to CSV/Excel |
| `/api/performance/health` | GET | System health |
| `/api/alerts/pending` | GET | Pending alerts |
| `/api/integrations/slack/alert` | POST | Send Slack alert |
| `/api/integrations/sheets/export-pilots` | POST | Export to Google Sheets |
| `/api/billing/plans` | GET | Get billing plans |
| `/api/billing/subscribe` | POST | Create subscription |

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete reference.

---

## 📊 Database Schema

### SQLite Databases

**clariq_pilots.sqlite**
- `pilots`: id, name, email, store_name, platform, status, created_at, contacted_at, completed_at

**clariq_actions.sqlite**
- `actions`: id, pilot_id, type, quantity, metadata, created_at
- `action_summary`: pilot_id, reorder_count, discount_count, promotion_count, query_count

**clariq_roi_params.sqlite**
- `roi_parameters`: pilot_id, cost_per_pilot, discount_cost_pct, promotion_cost_pct, updated_at

**clariq_performance_metrics.sqlite**
- `api_metrics`: endpoint, method, status_code, response_time_ms, created_at
- `system_metrics`: cpu_percent, memory_percent, disk_percent, uptime_hours, created_at

**clariq_alerts.sqlite**
- `alerts`: pilot_id, milestone_key, value_achieved, threshold, sent, created_at, sent_at
- `alert_subscriptions`: pilot_id, email, milestone_key, enabled, created_at

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest -v

# Specific test class
pytest -v backend/tests/test_api.py::TestPilots

# With coverage
pytest --cov=backend backend/tests/

# Performance tests
pytest -v backend/tests/test_api.py::TestPerformanceAndLoad
```

### Test Coverage

- ✅ Unit tests (50+ test cases)
- ✅ Integration tests (database, APIs)
- ✅ Performance tests (response time, load)
- ✅ Security tests (SQL injection, CORS, rate limiting)
- ✅ Error handling tests

---

## 📚 Documentation

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[.env.production.example](.env.production.example)** - Environment configuration
- **[scripts/backup.sh](scripts/backup.sh)** - Database backup script

---

## 🔧 Configuration

### Environment Variables

```bash
# Application
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=sqlite:///./data/clariq.db
POSTGRES_HOST=postgres
POSTGRES_USER=clariq
POSTGRES_PASSWORD=<password>

# Snowflake (optional)
SNOWFLAKE_ACCOUNT=<account>
SNOWFLAKE_USER=<user>
SNOWFLAKE_PASSWORD=<password>

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<password>

# Slack (optional)
SLACK_BOT_TOKEN=xoxb-<token>
SLACK_CHANNEL=#alerts

# Google Sheets (optional)
GOOGLE_SHEETS_CREDENTIALS=<json>
GOOGLE_SHEETS_SPREADSHEET_ID=<id>

# Shopify (optional)
SHOPIFY_API_KEY=<key>
SHOPIFY_API_PASSWORD=<password>

# Stripe (optional)
STRIPE_SECRET_KEY=sk_live_<key>
STRIPE_PUBLISHABLE_KEY=pk_live_<key>

# Security
JWT_SECRET=<secret>
API_KEY_SECRET=<secret>
```

---

## 🌐 Frontend

The dashboard is a single-page application (SPA) built with vanilla JavaScript.

### Features

- **Dark Mode** - Toggle with 🌙 Dark Mode button
- **Advanced Filtering** - Filter pilots by status, revenue, ROI
- **Bulk Actions** - Export/email multiple pilots at once
- **Mobile Responsive** - Works on tablets and phones
- **Real-time Updates** - Live data without page reload
- **Modal Dialogs** - Advanced export, milestone viewer, reports

### Pages

- **Home** - Dashboard overview with key metrics
- **Pilot Applicants** - Pilot management and comparison
- **ROI Analytics** - Profitability analysis
- **Performance** - System health and API metrics
- **Alerts** - Milestone tracking and notifications
- **Reports** - Report generation and scheduling
- **Billing** - Subscription management
- **Integrations** - Connect Slack, Google Sheets, etc

---

## 🚢 Deployment

### Quick Deploy to Railway.app

```bash
railway up
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Docker Compose (self-hosted)
- AWS ECS + ALB
- DigitalOcean App Platform
- Railway.app
- Security hardening
- SSL/TLS setup
- Database backups

---

## 🔒 Security

- ✅ JWT authentication
- ✅ HTTPS/SSL encryption
- ✅ SQL injection prevention
- ✅ CORS configuration
- ✅ Rate limiting
- ✅ Request validation
- ✅ Password hashing (bcrypt)
- ✅ Environment variable secrets

---

## 📈 Performance

- **API Response Time**: <200ms (p95)
- **Database Queries**: <50ms average
- **Concurrent Users**: 100+
- **Uptime**: 99.9%

---

## 🤝 Contributing

### Setup Development Environment

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/clariq.git
cd clariq

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Install dev dependencies
pip install -r backend/requirements.txt

# 4. Make changes and commit
git add .
git commit -m "feat: Add my feature"

# 5. Run tests
pytest -v

# 6. Push and create PR
git push origin feature/my-feature
```

### Commit Message Format

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
test: Add tests
chore: Update dependencies
```

---

## 📞 Support

- **Email**: support@clariq.com
- **Slack**: [Join Slack Community](https://clariq-community.slack.com)
- **Documentation**: https://docs.clariq.com
- **Issues**: GitHub Issues

---

## 📄 License

MIT License - see LICENSE file

---

## 🎉 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Snowflake](https://www.snowflake.com/) - Cloud data warehouse
- [Stripe](https://stripe.com/) - Payment processing
- [Slack](https://slack.com/) - Team communication
- [Shopify](https://www.shopify.com/) - E-commerce platform

---

**Made with ❤️ by the CLARIQ Team**

Last updated: July 2024
