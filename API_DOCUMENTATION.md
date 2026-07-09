# CLARIQ API Documentation

Complete REST API reference for the CLARIQ Pilot Program Management Platform.

---

## Overview

**Base URL:** `https://api.clariq.com`  
**Authentication:** JWT Token (Authorization: Bearer {token})  
**Response Format:** JSON  
**Rate Limit:** 100 requests/second

---

## Authentication

### Login
```
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

## Pilot Management

### Get All Pilots
```
GET /api/pilot
Authorization: Bearer {token}

Response:
{
  "pilots": [
    {
      "id": 1,
      "name": "John's Store",
      "email": "john@example.com",
      "store_name": "John's Fashion",
      "platform": "shopify",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "contacted_at": "2024-01-16T14:22:00Z",
      "completed_at": null
    }
  ],
  "total": 12,
  "page": 1
}
```

### Get Single Pilot
```
GET /api/pilot/{pilot_id}

Response:
{
  "id": 1,
  "name": "John's Store",
  "email": "john@example.com",
  "store_name": "John's Fashion",
  "platform": "shopify",
  "status": "active",
  "notes": "High engagement pilot",
  "created_at": "2024-01-15T10:30:00Z",
  "revenue": 5250.00,
  "roi_percent": 850,
  "reorder_count": 42
}
```

### Create Pilot
```
POST /api/pilot
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Jane's Boutique",
  "email": "jane@example.com",
  "store_name": "Jane's Fashion",
  "platform": "shopify",
  "store_url": "https://janes-boutique.myshopify.com"
}

Response: 201 Created
{
  "id": 13,
  "name": "Jane's Boutique",
  "status": "new"
}
```

### Update Pilot
```
PUT /api/pilot/{pilot_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "contacted",
  "notes": "Scheduled call for next week"
}

Response: 200 OK
```

---

## Analytics & ROI

### Get Pilot ROI
```
GET /api/roi/pilot/{pilot_id}

Response:
{
  "pilot_id": 1,
  "revenue_metrics": {
    "order_count": 42,
    "avg_order_value": 125.00,
    "estimated_cogs": 2100.00,
    "gross_profit": 3150.00,
    "gross_margin": 60.0
  },
  "investment_metrics": {
    "cost_per_pilot": 500.00,
    "pilot_product_cost": 50.00,
    "discount_cost": 315.00,
    "promotion_cost": 200.00,
    "total_investment": 1065.00
  },
  "profit_metrics": {
    "gross_profit": 3150.00,
    "net_profit": 2085.00,
    "profit_margin": 39.7
  },
  "roi_metrics": {
    "roi_percent": 195.8,
    "roi_status": "Highly profitable",
    "payback_period_days": 12,
    "break_even_reorders": 8
  }
}
```

### Get Program ROI
```
GET /api/roi/program

Response:
{
  "total_pilots": 12,
  "total_revenue": 45320.00,
  "total_profit": 32100.00,
  "avg_roi": 285.3,
  "profitability_rate": 91.7,
  "tier_distribution": {
    "exceptional": 8,
    "strong": 3,
    "positive": 1,
    "break_even": 0,
    "loss": 0
  }
}
```

### Pilot Comparison
```
GET /api/roi/comparison

Response:
[
  {
    "rank": 1,
    "pilot_id": 5,
    "name": "Top Store Inc",
    "revenue": 12500.00,
    "net_profit": 10200.00,
    "roi_percent": 2040,
    "profit_tier": "Exceptional",
    "days_active": 45,
    "reorders": 120
  },
  ...
]
```

### Forecast ROI
```
GET /api/analytics/forecast/{pilot_id}?days=30

Response:
{
  "pilot_id": 1,
  "current_roi": 195.8,
  "forecast": {
    "days_30": 240.5,
    "days_60": 287.3,
    "days_90": 340.2
  },
  "trend": "increasing",
  "confidence": 0.87,
  "growth_rate": 0.0145
}
```

### Churn Prediction
```
GET /api/analytics/churn/{pilot_id}

Response:
{
  "pilot_id": 1,
  "churn_probability": 0.25,
  "churn_risk_level": "low",
  "days_inactive": 3,
  "frequency_decline_pct": 10.5,
  "roi_status": "Profitable",
  "contributing_factors": [
    "Activity declining - offer support"
  ],
  "recommendation": "Monitor pilot"
}
```

### Benchmark
```
GET /api/analytics/benchmark/{pilot_id}

Response:
{
  "pilot_id": 1,
  "pilot_name": "John's Store",
  "benchmarks": {
    "revenue": {
      "pilot_value": 5250.00,
      "peer_average": 3780.00,
      "percentile": 76,
      "above_average": true
    },
    "roi": {
      "pilot_value": 195.8,
      "peer_average": 125.3,
      "percentile": 82,
      "above_average": true
    }
  },
  "performance_summary": "Top Performer"
}
```

---

## Export & Reporting

### Get Available Columns
```
GET /api/export/columns/{data_type}
# data_type: 'pilots' or 'actions'

Response:
{
  "columns": {
    "id": {"label": "ID", "type": "integer"},
    "name": {"label": "Pilot Name", "type": "string"},
    "email": {"label": "Email", "type": "string"},
    "revenue": {"label": "Revenue", "type": "currency"},
    "roi_percent": {"label": "ROI %", "type": "percentage"},
    ...
  }
}
```

### Export Pilots CSV
```
POST /api/export/pilots
Authorization: Bearer {token}
Content-Type: application/json

{
  "data_type": "pilots",
  "format": "csv",
  "columns": ["id", "name", "email", "revenue", "roi_percent", "status"]
}

Response: 200 OK
Content-Type: text/csv
Content-Disposition: attachment; filename="pilots.csv"

id,name,email,revenue,roi_percent,status
1,John's Store,john@example.com,5250.00,195.8,active
...
```

### Export Pilots Excel
```
POST /api/export/pilots
Authorization: Bearer {token}
Content-Type: application/json

{
  "data_type": "pilots",
  "format": "excel",
  "columns": ["id", "name", "email", "revenue", "roi_percent", "status"]
}

Response: 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="pilots.xlsx"
```

---

## Performance Monitoring

### System Health
```
GET /api/performance/health

Response:
{
  "overall_status": "healthy",
  "timestamp": "2024-01-20T15:45:30Z",
  "api_performance": {
    "total_requests": 15234,
    "avg_response_time_ms": 145.3,
    "p95_response_time_ms": 450.2,
    "error_rate": 0.8
  },
  "system_resources": {
    "cpu_percent": 32.5,
    "memory_percent": 58.3,
    "disk_percent": 45.1,
    "status": "healthy"
  },
  "database": {
    "pilot_count": 42,
    "action_count": 1250,
    "connections": 5,
    "status": "connected"
  },
  "sync_status": {
    "success_rate": 98.5,
    "last_sync": "2024-01-20T15:40:00Z"
  }
}
```

### API Metrics
```
GET /api/performance/api-metrics?hours=24

Response:
{
  "period_hours": 24,
  "total_requests": 15234,
  "avg_response_time_ms": 145.3,
  "p95_response_time_ms": 450.2,
  "max_response_time_ms": 2500.0,
  "error_rate": 0.8,
  "endpoints": {
    "/api/pilot": {
      "calls": 2340,
      "avg_response_time_ms": 120.5,
      "error_rate": 0.2
    },
    ...
  }
}
```

---

## Alerts & Milestones

### Get Pending Alerts
```
GET /api/alerts/pending

Response:
{
  "count": 3,
  "alerts": [
    {
      "alert_id": 42,
      "pilot_id": 5,
      "pilot_name": "Top Store Inc",
      "milestone_title": "10 Reorders",
      "value_achieved": 10,
      "threshold": 10,
      "created_at": "2024-01-20T10:00:00Z",
      "sent": false
    }
  ]
}
```

### Send Alert
```
POST /api/alerts/send/{alert_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "recipient_email": "manager@clariq.com"
}

Response:
{
  "success": true,
  "message": "Alert sent successfully",
  "sent_at": "2024-01-20T15:45:30Z"
}
```

### Get Milestones
```
GET /api/alerts/milestones

Response:
{
  "milestones": [
    {
      "key": "first_reorder",
      "title": "First Reorder",
      "emoji": "🎉",
      "type": "action",
      "threshold": 1
    },
    {
      "key": "ten_reorders",
      "title": "10 Reorders",
      "emoji": "🔟",
      "type": "action",
      "threshold": 10
    },
    ...
  ]
}
```

---

## Integrations

### Slack - Send Alert
```
POST /api/integrations/slack/alert
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "High Churn Risk",
  "message": "3 pilots at risk of churn",
  "severity": "warning"
}

Response:
{
  "success": true,
  "message": "Alert sent to Slack"
}
```

### Google Sheets - Export Pilots
```
POST /api/integrations/sheets/export-pilots
Authorization: Bearer {token}

Response:
{
  "success": true,
  "message": "Exported 42 pilots to Google Sheets",
  "worksheet": "Pilots",
  "row_count": 43
}
```

### Shopify - Webhook Status
```
GET /api/integrations/shopify/webhook/status

Response:
{
  "total_webhooks": 1245,
  "pending_webhooks": 12,
  "processed_webhooks": 1233,
  "by_topic": {
    "orders/create": 800,
    "customers/update": 345,
    "products/update": 100
  }
}
```

---

## Billing

### Get Plans
```
GET /api/billing/plans

Response:
{
  "plans": [
    {
      "id": "free",
      "name": "Free",
      "price": 0,
      "max_pilots": 2,
      "features": ["Basic analytics", "Email alerts"]
    },
    {
      "id": "starter",
      "name": "Starter",
      "price": 49,
      "max_pilots": 10,
      "features": ["Advanced ROI analytics", "Custom exports", ...]
    },
    ...
  ],
  "currency": "usd"
}
```

### Create Subscription
```
POST /api/billing/subscribe
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": "user123",
  "email": "user@example.com",
  "name": "John Doe",
  "plan": "starter"
}

Response:
{
  "success": true,
  "plan": "starter",
  "subscription_id": "sub_1234567890",
  "amount": 49,
  "message": "Subscription created for Starter plan"
}
```

### Get Subscription
```
GET /api/billing/subscription/{user_id}
Authorization: Bearer {token}

Response:
{
  "user_id": "user123",
  "plan": "starter",
  "status": "active",
  "max_pilots": 10,
  "features": [...],
  "price": 49
}
```

### Check Usage
```
GET /api/billing/usage/{user_id}
Authorization: Bearer {token}

Response:
{
  "user_id": "user123",
  "plan": "starter",
  "pilots_used": 8,
  "pilots_limit": 10,
  "usage_percentage": 80,
  "can_add_pilot": true
}
```

### Get Invoices
```
GET /api/billing/invoices/{user_id}
Authorization: Bearer {token}

Response:
{
  "user_id": "user123",
  "invoices": [
    {
      "invoice_id": "inv_1234567890",
      "amount": 49.00,
      "status": "paid",
      "paid_date": "2024-01-05T00:00:00Z",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "count": 5
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input",
  "errors": [
    {"field": "email", "message": "Invalid email format"}
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required",
  "error_code": "AUTH_REQUIRED"
}
```

### 404 Not Found
```json
{
  "detail": "Pilot not found",
  "error_code": "PILOT_NOT_FOUND"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

### 500 Server Error
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Rate Limiting

- **General API:** 100 requests/second per user
- **Export endpoints:** 10 requests/minute per user
- **Webhook endpoints:** No limit (trusted sources)

Headers returned:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705768800
```

---

## Webhooks

### Configure Webhook Endpoint
```
POST /api/webhooks/register
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://yourapp.com/webhooks/clariq",
  "events": ["pilot.created", "milestone.achieved", "alert.pending"]
}

Response:
{
  "webhook_id": "wh_1234567890",
  "url": "https://yourapp.com/webhooks/clariq",
  "events": ["pilot.created", "milestone.achieved", "alert.pending"],
  "secret": "whsec_1234567890"
}
```

### Webhook Events

**pilot.created**
```json
{
  "event": "pilot.created",
  "timestamp": "2024-01-20T15:45:30Z",
  "data": {
    "pilot_id": 42,
    "name": "New Store",
    "email": "owner@store.com"
  }
}
```

**milestone.achieved**
```json
{
  "event": "milestone.achieved",
  "timestamp": "2024-01-20T15:45:30Z",
  "data": {
    "pilot_id": 42,
    "milestone": "ten_reorders",
    "value": 10
  }
}
```

---

## SDKs & Libraries

- **JavaScript:** `npm install @clariq/sdk`
- **Python:** `pip install clariq-sdk`
- **Go:** `go get github.com/clariq/sdk-go`

---

## Support

- **Email:** support@clariq.com
- **Slack:** #clariq-support
- **Documentation:** https://docs.clariq.com
- **Status Page:** https://status.clariq.com
