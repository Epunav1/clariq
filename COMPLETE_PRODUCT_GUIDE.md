# Clariq - Complete Product & Technical Deep Dive

## 📚 Table of Contents
1. [What is Clariq? (Detailed)](#what-is-clariq-detailed)
2. [The Problem We Solve](#the-problem-we-solve)
3. [How Clariq Works](#how-clariq-works)
4. [User Journey](#user-journey)
5. [Feature Breakdown](#feature-breakdown)
6. [Business Model](#business-model)
7. [Technical Architecture](#technical-architecture)
8. [Data Flow](#data-flow)
9. [API Endpoints](#api-endpoints)
10. [Integration Points](#integration-points)
11. [Real-World Use Cases](#real-world-use-cases)
12. [Competitive Advantages](#competitive-advantages)
13. [Code Structure Guide](#code-structure-guide)
14. [Scalability & Performance](#scalability--performance)
15. [Future Roadmap](#future-roadmap)

---

## What is Clariq? (Detailed)

### The Elevator Pitch
Clariq is an **AI-powered natural language analytics platform** for e-commerce sellers. Instead of juggling multiple dashboards, learning SQL, or wading through spreadsheets, sellers simply ask Clariq questions in plain English and get instant, actionable insights powered by AI.

### The Long Version
Imagine you're running a business selling products across Amazon, Shopify, and TikTok Shop simultaneously. You have thousands of orders, hundreds of products, tens of thousands of customers. Your data is scattered:
- Shopify has sales data
- Amazon has marketplace metrics
- TikTok Shop has engagement data
- Your email platform has customer lifecycle data
- Your accounting software has financial data

**Without Clariq:**
- You log into 5+ different dashboards
- Each dashboard uses different terminology and metrics
- To answer "Which products are trending?" you need to:
  1. Check Shopify Dashboard for top sellers
  2. Check Amazon Seller Central for bestsellers
  3. Check TikTok Shop performance
  4. Cross-reference in a spreadsheet
  5. Do manual calculations
  6. Time wasted: 30+ minutes

**With Clariq:**
- You ask: "Which products are trending across my stores?"
- Clariq's AI queries all connected platforms
- Returns answer in 3 seconds: "Your top 5 trending products are..."
- Includes insights like revenue impact, growth rate, competitor context

That's Clariq.

### Core Premise
**Natural language is the future of business intelligence.** Non-technical users (store owners, operators, accountants) shouldn't need to learn SQL or Python to understand their own data. They should be able to ask questions the way they'd ask a human analyst.

---

## The Problem We Solve

### Problem 1: Dashboard Fragmentation
**The Challenge:** E-commerce sellers use 5-10+ platforms:
- Shopify / WooCommerce / Etsy (storefront)
- Amazon Seller Central (marketplace)
- TikTok Shop (emerging channel)
- Alibaba / Jumia (international)
- Email platforms (customer data)
- Accounting software (financial data)

Each has its own dashboard, terminology, and export format.

**The Cost:**
- Time wasted context-switching (estimated 8+ hours/week)
- Manual data consolidation in Excel (error-prone)
- Missed insights because data is siloed
- Delayed decision-making

**Clariq's Solution:** Single interface, unified data, instant answers

### Problem 2: Analysis Paralysis
**The Challenge:** When data is hard to access, sellers don't ask questions.
- "How's my cash flow really?" → Too complex to check
- "Which customers are at churn risk?" → Would need hours of Excel work
- "What's my actual unit economics?" → Requires SQL knowledge

**The Cost:**
- Businesses fly blind, making decisions on gut feel
- Missed revenue opportunities
- Poor inventory management
- Inefficient marketing spend

**Clariq's Solution:** Make analysis so easy you do it daily

### Problem 3: Knowledge Gap
**The Challenge:** Most e-commerce operators aren't data analysts.
- Don't know SQL
- Don't understand database schemas
- Aren't comfortable with BI tools like Tableau or Looker
- These tools are also $$$

**The Cost:**
- Have to hire a data analyst (cost: $60K-$120K/year)
- Or outsource analytics (cost: $2K-$5K/month)
- Still slow turnaround on custom reports

**Clariq's Solution:** AI that understands business language → SQL translation

---

## How Clariq Works

### The Pipeline (High Level)

```
User Question 
    ↓
Natural Language Processing (NLP)
    ↓
Intent Recognition ("Find trending products")
    ↓
SQL/Query Generation (AI → SQL)
    ↓
Data Retrieval (Query Snowflake/SQLite)
    ↓
Result Formatting & Enhancement
    ↓
AI-Powered Insights (not just data, but meaning)
    ↓
Display to User
```

### Step-by-Step Example

**User Asks:** "Which of my Amazon products are underperforming compared to last month?"

**Step 1: NLP Processing**
- Extract entities: "Amazon", "products", "underperforming", "last month"
- Identify metric: sales/revenue/conversion
- Identify comparison: month-over-month

**Step 2: SQL Generation**
Clariq's AI generates:
```sql
SELECT 
  product_id,
  product_name,
  SUM(sales_current_month) as current_sales,
  SUM(sales_last_month) as last_sales,
  ((current_sales - last_sales) / last_sales) * 100 as pct_change
FROM amazon_products
WHERE pct_change < -20  -- 20%+ decline
ORDER BY pct_change ASC
```

**Step 3: Execute Query**
- Query Snowflake (or SQLite) database
- Get back 47 products with >20% sales decline

**Step 4: Enhance Results**
AI adds context:
- "Your SKU X-123 dropped 45% - likely due to price increase on 7/3"
- "SKU Y-456 down 32% - similar products seeing 10% decline (market-wide)"
- "Recommendation: Re-examine pricing or improve product listing"

**Step 5: Return to User**
```json
{
  "answer": "47 products underperforming vs last month",
  "data": [
    {
      "sku": "X-123",
      "name": "Premium Widget",
      "decline": "-45%",
      "likely_cause": "Price increase on 7/3",
      "recommendation": "Consider discount or promotion"
    },
    ...
  ],
  "insights": [
    "Overall, your store is down 12% MoM",
    "Underperforming products account for $8,400 lost revenue",
    "3 of 10 bestsellers are in decline - prioritize"
  ]
}
```

---

## User Journey

### Phase 1: Discovery & Sign Up
1. User lands on `tryclariq.com`
2. Sees animated landing page
3. Clicks "Start free trial" → Sign up page
4. Fills form: name, email, password
5. Clicks "Create account" → Instant 7-day trial activated

**Current Experience:** 
- Landing is beautiful (splash + intro animations)
- All nav items clickable (Product, Pricing, About, Support)
- Sign-up process is simple, 3 fields

### Phase 2: Store Connection
1. User logs into Clariq dashboard (`index.html` post-login view)
2. Sees "Connect your first store" button
3. Selects platform: Shopify, Amazon, WooCommerce, etc.
4. OAuth flow redirects to store platform
5. User authorizes Clariq to read-only access
6. Clariq syncs last 30/60/90 days of data

**Technical Flow:**
- `POST /api/connect/shopify` - Initiates OAuth
- Stores connection token in database
- Background job (`shopify_sync.py`) runs every 60 min to sync data
- Data stored in SQLite or Snowflake

### Phase 3: Asking Questions
1. User opens Clariq dashboard
2. See search/chat interface
3. Types question: "What's my revenue by product category?"
4. Hits enter
5. Query routes to `POST /api/query`
6. Natural language → SQL conversion happens
7. Query executed against connected store data
8. Results return in 2-3 seconds
9. User sees data + insights + recommendations

**Current Flow:**
- Frontend collects question via text input
- Sends to `routes/query.py`
- `ai/nl_to_sql.py` converts NL to SQL using LLM
- Query executed on database
- Results formatted and returned as JSON

### Phase 4: Taking Action
1. User sees insights
2. Makes business decision:
   - "My top 3 products account for 60% of revenue" → Focus marketing budget there
   - "Customers in South region have 2x churn" → Launch targeted retention campaign
   - "Inventory for product X runs out every 3 days" → Increase stock orders
3. Takes action in their own store or Clariq (if we build action features)

---

## Feature Breakdown

### Current Features (MVP)

#### 1. Multi-Platform Connection
- Shopify
- Amazon Seller Central
- TikTok Shop
- Alibaba
- Jumia
- WooCommerce
- Etsy
- More coming...

**How it works:**
- Each platform has OAuth flow
- Clariq reads: Orders, Products, Customers, Inventory, Reviews
- Data synced every 60-120 minutes via background jobs
- All data stored locally (encrypted)

**Code Location:** `routes/connections.py`

#### 2. Natural Language Query Interface
- User types questions in plain English
- AI converts to SQL
- Results returned with insights

**Examples of Questions:**
- "Show my top 10 products by revenue"
- "Which customers haven't purchased in 30+ days?"
- "What's my average order value by region?"
- "Compare my June sales to May"
- "Which products have reviews below 4 stars?"

**Code Location:** `routes/query.py`, `ai/nl_to_sql.py`

#### 3. Data Visualization
- Tables with sortable columns
- Charts (revenue trends, product rankings)
- Comparison views (this month vs last month)
- Heatmaps (customer activity by region)

**Current Status:** Backend returns JSON data; frontend displays in tables

**Code Location:** `index.html` (would need charting library like Chart.js)

#### 4. Smart Recommendations
- AI suggests questions user might want to ask
- "Your best-performing products are X, Y, Z - should you increase marketing?"
- "You have 47 abandoned carts totaling $12K - want to run email campaign?"
- "Inventory for 5 products will run out in <7 days"

**Code Location:** `routes/recommendations.py`

#### 5. Saved Queries & Reports
- User can save favorite queries
- Schedule reports to email (e.g., "weekly revenue summary")
- Share reports with team members

**Current Status:** Basic structure in place; email integration pending

**Code Location:** `routes/upload.py` (file storage); background jobs for scheduling

#### 6. Team Collaboration
- Multiple users per account (Enterprise plan)
- Different permission levels
- Audit log of who queried what

**Current Status:** Basic user auth; multi-user not yet implemented

**Code Location:** `routes/auth_clean.py`, `routes/auth.py`

#### 7. Mobile Support
- Mobile-responsive landing page
- Dashboard accessible on tablet/phone (not optimized yet)

**Code Location:** `index.html` (responsive CSS with media queries)

---

## Business Model

### Revenue Streams

#### Subscription (Primary)
Three tiers:

| Tier | Price | Users | Stores | Features |
|------|-------|-------|--------|----------|
| **Starter** | Free | 1 | 1 | 500 questions/month, 30-day history, email support |
| **Pro** | $99/month | 1 | 5 | Unlimited questions, full history, priority support, team access (2 seats) |
| **Enterprise** | $249/month | Unlimited | Unlimited | Everything, +dedicated account manager, custom integrations |

#### Usage-Based Pricing (Future)
- Questions beyond limit: $0.10-$0.25/question
- Premium AI features: +$29/month for advanced insights
- Custom reports: $199/project

#### Data Services (Future)
- Anonymized market benchmarks: "Your store is in top 25% for AOV"
- Competitive intelligence: "What are competitors charging?"
- Industry insights: "Best practices from top sellers in your niche"

### Unit Economics (Estimated)

| Metric | Value |
|--------|-------|
| Monthly Subscription Revenue (Target Year 1) | $50K |
| Customer Acquisition Cost (CAC) | $250 |
| Lifetime Value (LTV) | $4,500 (45 months @ $99 avg) |
| LTV:CAC Ratio | 18:1 ✅ (healthy) |
| Gross Margin | 85% (AI costs ~15% of revenue) |

### Go-to-Market Strategy

**Phase 1 (Current):** Free trial + landing page
- Drive traffic via content marketing
- Focus on SEO ("how to analyze e-commerce data")
- Landing page tells the story

**Phase 2:** Influencer partnerships
- Partner with top Shopify/Amazon creators
- Give them free Enterprise accounts
- Generate social proof

**Phase 3:** B2B partnerships
- WhiteLabel for e-commerce platforms
- "Amazon Seller Central + Clariq" integration
- Revenue share model

---

## Technical Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     USERS (E-commerce Sellers)              │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              RENDER STATIC SITE (clariq-web)                │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  index.html - Landing Page + Dashboard              │   │
│  │  - Multi-page app (home, product, pricing, etc)    │   │
│  │  - Splash/Intro animations                          │   │
│  │  - API integration with backend                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  Status: LIVE at www.tryclariq.com                          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ↓
┌─────────────────────────────────────────────────────────────┐
│           RENDER WEB SERVICE (clariq-api)                    │
│                                                               │
│  FastAPI App (main.py)                                      │
│  ├─ Authentication Routes (JWT, OAuth)                     │
│  ├─ Query Processing (NL→SQL)                              │
│  ├─ Platform Connections (Shopify, Amazon, etc)            │
│  ├─ Data Synchronization (background jobs)                 │
│  ├─ Billing Integration (Stripe)                           │
│  └─ Health Checks & Monitoring                             │
│                                                               │
│  Status: LIVE at api.tryclariq.com                          │
└────────────┬─────────────────────────────────┬──────────────┘
             │                                 │
        HTTP/REST                         Background Jobs
             ↓                                 ↓
    ┌────────────────┐             ┌──────────────────────┐
    │   DATABASES    │             │   APSCHEDULER        │
    │                │             │                      │
    │ SQLite (Main)  │             │ - Shopify Sync (60m) │
    │ Snowflake (Opt)│             │ - Amazon Sync (120m) │
    │                │             │ - Report Send (1x/wk)│
    └────────────────┘             │ - Milestones (30m)  │
                                   └──────────────────────┘
             ↓                              ↓
        ┌─────────────────────────────────────────┐
        │  EXTERNAL SERVICES (All Optional)        │
        │                                         │
        │  - Anthropic API (AI/LLM)              │
        │  - Shopify OAuth & API                 │
        │  - Amazon MWS API                      │
        │  - Stripe Billing                      │
        │  - Email Service (SendGrid)            │
        └─────────────────────────────────────────┘
```

### Layer Breakdown

#### Layer 1: Presentation (Frontend)
- **Technology:** HTML5 + CSS3 + Vanilla JavaScript
- **Hosted:** Render Static Site
- **Responsibilities:**
  - Landing page design
  - Post-login dashboard
  - Question input interface
  - Results visualization
  - Page routing

#### Layer 2: API Gateway & Business Logic (Backend)
- **Technology:** FastAPI + Uvicorn
- **Hosted:** Render Web Service
- **Responsibilities:**
  - Route definitions
  - Request/response handling
  - Authentication/Authorization
  - Query processing pipeline
  - Database interactions

#### Layer 3: AI/ML Pipeline
- **Technology:** Anthropic Claude API + sklearn/pandas
- **Responsibilities:**
  - Natural language understanding
  - Intent extraction
  - SQL generation
  - Result ranking/filtering
  - Insight generation

#### Layer 4: Data Layer
- **Primary DB:** SQLite (persistent filesystem on Render)
- **Warehouse:** Snowflake (optional, for scale)
- **Responsibilities:**
  - User data storage
  - Store connection credentials
  - Query results caching
  - Historical data
  - User settings/preferences

#### Layer 5: Integration Layer
- **OAuth providers:** Shopify, Amazon, TikTok, Etsy
- **Payment:** Stripe
- **Scheduling:** APScheduler
- **Communication:** Email service

---

## Data Flow

### 1. Initial Store Connection

```
User clicks "Connect Shopify Store"
  ↓
Frontend redirects to Shopify OAuth
  ↓
Shopify asks: "Does Clariq want to access your store?"
  ↓
User clicks "Approve"
  ↓
Shopify redirects back to Clariq with authorization code
  ↓
Backend exchanges code for access token
  ↓
Token stored securely in database (encrypted)
  ↓
Background job triggered: Full historical data sync
  ↓
Shopify API called: GET /admin/api/2024-01/orders.json?limit=100
  ↓
Results: Last 100 orders with full details (customer, products, price, etc)
  ↓
Data transformed and stored in SQLite
  ↓
Process repeats for Products, Customers, Inventory, Reviews
  ↓
User sees dashboard: "Shopify store synced! You have 2,847 orders"
```

**Code Location:** `routes/connections.py`, `shopify_sync.py`

### 2. Asking a Question

```
User types: "Show me my top 5 products by revenue"
  ↓
Frontend submits POST /api/query
  Body: { question: "Show me my top 5 products by revenue", store_id: "shopify_123" }
  ↓
Backend receives request at routes/query.py
  ↓
Call Anthropic API:
  "Convert this question to SQL: 'Show me my top 5 products by revenue'"
  ↓
Anthropic returns SQL:
  SELECT product_id, product_name, SUM(price * quantity) as revenue
  FROM orders
  GROUP BY product_id
  ORDER BY revenue DESC
  LIMIT 5
  ↓
Backend executes SQL against SQLite database
  ↓
Results come back: [
    { product_id: 1, product_name: "Widget A", revenue: 45000 },
    { product_id: 2, product_name: "Widget B", revenue: 38000 },
    ...
  ]
  ↓
Backend enriches results with insights:
  - Calculates percentage of total revenue each product represents
  - Identifies trends (is it up from last week?)
  - Generates recommendation
  ↓
Return JSON response to frontend:
  {
    success: true,
    data: [ ... ],
    insights: [
      "Product A represents 28% of your revenue",
      "Revenue up 15% from last week"
    ],
    next_questions: [
      "Show reviews for top product",
      "Which regions buy most of product A?"
    ]
  }
  ↓
Frontend receives response
  ↓
Renders table with results
  ↓
User sees answer with insights in <3 seconds
```

**Code Location:** `routes/query.py`, `ai/nl_to_sql.py`

### 3. Background Data Sync

```
Every 60 minutes (Shopify):
  ↓
APScheduler triggers job: "sync_shopify_stores"
  ↓
Loop through all users with active Shopify connections
  ↓
For each user:
    - Use stored OAuth token to call Shopify API
    - Fetch orders from last 60 minutes
    - Fetch updated product inventory
    - Fetch new customer data
    - Transform and upsert into SQLite
    ↓
Update last_sync_time in database
  ↓
If errors occur:
    - Log to monitoring system
    - Send alert to admin
    - Continue (don't crash)
  ↓
Job completes
```

**Code Location:** `shopify_sync.py`, `main.py` (lifespan context with APScheduler)

---

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/register
**Register a new user**
```json
Request:
{
  "email": "seller@example.com",
  "password": "securepassword123",
  "name": "John Seller"
}

Response (201 Created):
{
  "user_id": "user_abc123",
  "email": "seller@example.com",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "trial_days_remaining": 7
}
```

#### POST /api/auth/login
**Log in existing user**
```json
Request:
{
  "email": "seller@example.com",
  "password": "securepassword123"
}

Response (200 OK):
{
  "user_id": "user_abc123",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "plan": "pro"
}
```

### Connection Endpoints

#### GET /api/connections
**List connected stores**
```json
Response (200 OK):
{
  "connections": [
    {
      "id": "conn_123",
      "platform": "shopify",
      "store_name": "mystore.myshopify.com",
      "connected_at": "2024-07-01T10:30:00Z",
      "last_sync": "2024-07-10T14:25:00Z",
      "status": "active"
    },
    {
      "id": "conn_124",
      "platform": "amazon",
      "store_name": "AXXXXXXXXXXXX",
      "connected_at": "2024-07-02T09:15:00Z",
      "last_sync": "2024-07-10T14:20:00Z",
      "status": "active"
    }
  ]
}
```

#### POST /api/connections/shopify/oauth
**Initiate Shopify OAuth flow**
```json
Request:
{
  "shop": "mystore.myshopify.com"
}

Response (200 OK):
{
  "oauth_url": "https://mystore.myshopify.com/admin/oauth/authorize?..."
}
```

#### POST /api/connections/shopify/callback
**Handle Shopify OAuth callback**
```json
Request:
{
  "code": "authorization_code_from_shopify",
  "shop": "mystore.myshopify.com"
}

Response (201 Created):
{
  "connection_id": "conn_123",
  "platform": "shopify",
  "status": "syncing",
  "message": "Store connected! Syncing your data..."
}
```

### Query Endpoints

#### POST /api/query
**Ask a question about your data**
```json
Request:
{
  "question": "What are my top 5 products by revenue?",
  "connection_id": "conn_123",
  "filters": {
    "date_range": "last_30_days"
  }
}

Response (200 OK):
{
  "success": true,
  "question": "What are my top 5 products by revenue?",
  "generated_sql": "SELECT product_name, SUM(price*qty) as revenue FROM orders WHERE created_at > NOW() - INTERVAL 30 day GROUP BY product_name ORDER BY revenue DESC LIMIT 5",
  "results": [
    {
      "product_name": "Premium Widget",
      "revenue": 45230.50,
      "units_sold": 152,
      "avg_price": 297.57,
      "trend": "up 12% from last period"
    },
    ...
  ],
  "insights": [
    "Your top product represents 28% of total revenue",
    "Revenue is up 15% compared to last month",
    "These 5 products account for 63% of your total sales"
  ],
  "suggested_follow_ups": [
    "Show me the reviews for these products",
    "Which regions are buying these products most?",
    "What's the profit margin on these?"
  ],
  "execution_time_ms": 342
}
```

#### POST /api/query/save
**Save a frequently asked question**
```json
Request:
{
  "question": "What are my top 5 products by revenue?",
  "name": "Top Products Report",
  "connection_id": "conn_123"
}

Response (201 Created):
{
  "saved_query_id": "sq_456",
  "name": "Top Products Report",
  "created_at": "2024-07-10T15:30:00Z"
}
```

#### GET /api/query/saved
**List saved queries**
```json
Response (200 OK):
{
  "saved_queries": [
    {
      "id": "sq_456",
      "name": "Top Products Report",
      "question": "What are my top 5 products by revenue?",
      "created_at": "2024-07-10T15:30:00Z",
      "last_run": "2024-07-10T14:00:00Z",
      "run_count": 23
    }
  ]
}
```

#### GET /api/query/saved/{query_id}
**Run a saved query**
```json
Response (200 OK):
{
  "query_id": "sq_456",
  "results": [ ... ],
  "executed_at": "2024-07-10T16:00:00Z",
  "execution_time_ms": 287
}
```

### Health & System Endpoints

#### GET /api/health
**Health check**
```json
Response (200 OK):
{
  "api": "healthy",
  "database": "connected",
  "snowflake": "connected",
  "uptime_seconds": 864000,
  "timestamp": "2024-07-10T16:00:00Z"
}
```

---

## Integration Points

### 1. E-Commerce Platforms

#### Shopify Integration
- **Flow:** OAuth → API access → Data sync
- **Data Synced:** Orders, Products, Customers, Inventory, Fulfillments
- **Sync Interval:** Every 60 minutes
- **API Used:** Shopify Admin API v2024-01
- **Rate Limits:** 2 requests/second

**Code:** `routes/connections.py`, `shopify_sync.py`

#### Amazon Integration
- **Flow:** MWS credentials → API access → Data sync
- **Data Synced:** Orders, Products, Inventory, Fulfillments, Feedback
- **Sync Interval:** Every 120 minutes (heavier API usage)
- **API Used:** Amazon Marketplace Web Service (MWS)
- **Rate Limits:** 15 requests/minute for reports

**Code:** `routes/connections.py`, background job in `main.py`

#### TikTok Shop Integration
- **Flow:** OAuth → API access → Data sync
- **Data Synced:** Orders, Products, Shop stats
- **Sync Interval:** Every 60 minutes
- **API Used:** TikTok Shop Open API

**Code:** `routes/connections.py`

### 2. AI/LLM Integration

#### Anthropic Claude API
- **Purpose:** NL → SQL conversion, insights generation
- **Model Used:** Claude 3.5 Sonnet
- **Usage Pattern:**
  1. User asks question
  2. Send to Claude: "Convert to SQL"
  3. Claude returns SQL query
  4. Execute SQL
  5. Send results + ask Claude for insights
  6. Claude returns human-readable insights

**Code:** `ai/nl_to_sql.py`, `routes/query.py`

**Example Prompt:**
```
You are an e-commerce data analyst. Convert the following question to SQL.

Database schema:
- orders (id, customer_id, product_id, quantity, price, created_at)
- products (id, name, category, price, cost)
- customers (id, email, region, created_at)

User question: "Which products are trending in the West region?"

Return ONLY valid SQL, no explanation.
```

### 3. Payment Integration

#### Stripe
- **Purpose:** Billing, subscription management
- **Flow:**
  1. User upgrades to paid plan
  2. Frontend redirects to Stripe checkout
  3. User enters card details on Stripe (PCI compliant)
  4. Stripe returns token
  5. Backend charges card
  6. Webhook updates user plan in database
  
**Code:** `routes/billing.py`

### 4. Job Scheduling

#### APScheduler
- **Purpose:** Background synchronization
- **Jobs:**
  - `sync_shopify_stores` - Every 60 minutes
  - `sync_amazon_stores` - Every 120 minutes
  - `send_weekly_reports` - Tuesdays 9 AM UTC
  - `check_milestones` - Every 30 minutes

**Code:** `main.py` (lifespan context manager with scheduler)

### 5. Database Integration

#### SQLite (Production Primary)
- **Path:** `backend/data/clariq.db`
- **Persistent:** ✅ Survives Render restarts
- **Used For:** All operational data (users, connections, queries, results)

#### Snowflake (Optional Enterprise)
- **Purpose:** Large-scale data warehousing
- **Used For:** Historical data, complex analytics
- **Optional:** App works fine without it

**Code:** `db/snowflake_client.py` (optional wrapper)

---

## Real-World Use Cases

### Use Case 1: Solopreneur Shopify Seller

**Who:** Sarah runs a single Shopify store selling handmade jewelry. $50K/month revenue.

**Before Clariq:**
- Logs into Shopify admin daily
- Manually checks "Sales by Product" report
- Exports to Excel to calculate margins
- Checks Facebook for order notes
- Time spent: 45 min/day = ~3.75 hours/week

**With Clariq:**
- Morning: Asks "What were my top 3 products yesterday?"
- Gets answer + insights in 3 seconds
- Sees margin, customer feedback, trends
- Asks: "Which products are low stock?"
- Takes action: Orders inventory
- Time spent: 10 min/day = ~50 min/week

**Value:** Saves 3+ hours/week, makes better decisions, scales faster

---

### Use Case 2: Multi-Platform Agency

**Who:** Mike manages 12 Shopify stores for different clients. $500K/month aggregate revenue.

**Before Clariq:**
- 12 separate Shopify dashboards
- Manually creates reports for each client
- Cross-references data across platforms
- Updates spreadsheet with metrics
- Creates PowerPoint for client meetings
- Time spent: 20 hours/week

**With Clariq:**
- Client 1: "Show me my performance vs last month"
- Answer in 3 seconds with all metrics
- Client 2: "Why are conversions down?"
- AI analyzes: Traffic is up, but AOV is down → UX issue
- Client 3: "Which products should I feature?"
- Answer with data: "These 5 products have 4.8+ stars and fast shipping"
- Generates client-ready report with 1 click
- Time spent: 4 hours/week

**Value:** 16 hours/week saved, better insights, scales without hiring

---

### Use Case 3: Enterprise Multi-Channel Brand

**Who:** Large apparel brand sells on Shopify, Amazon, TikTok, Alibaba. $10M/year.

**Before Clariq:**
- 5+ dashboards, each with different terminology
- Data analyst job: $90K/year
- Analyst spends 40 hours/week making reports
- Reports take 2-3 days to deliver
- Executives can't get ad-hoc insights
- Business decisions delayed

**With Clariq:**
- CFO asks: "What's our actual COGS per unit across all channels?"
- Clariq queries all 4 platforms, calculates, returns in seconds
- CEO asks: "Which region has highest churn?"
- Answer with data + recommendation for retention campaign
- Marketing director asks: "Which campaigns drive highest LTV customers?"
- Clariq correlates ad spend with customer lifetime value
- Finance team gets monthly profitability report auto-emailed
- Still employs 1 analyst, but now they work on strategy instead of data gathering

**Value:** Analyst time reallocated to strategy, insights in real-time, agile decision making

---

## Competitive Advantages

### 1. Natural Language Interface
- **vs Tableau/Looker:** Don't require SQL knowledge
- **vs BI Dashboards:** Instant answers vs manual report creation
- **vs Human Analyst:** 10x faster, always available

### 2. Multi-Platform Native
- **vs Single-Platform Tools:** Connect 7+ platforms
- **vs Manual Consolidation:** Automatic syncing
- **vs Expensive Data Engineers:** AI handles integration

### 3. AI-Powered Insights
- **vs Raw Data:** Contextual recommendations included
- **vs Generic Reports:** Personalized to your data patterns
- **vs SQL Queries:** No SQL required

### 4. Freemium Model
- **Trial user:** Immediate value (7 days free)
- **Pro conversion:** Easy upgrade for serious users
- **Enterprise:** Custom solutions for big budgets

### 5. Perfect Pricing Point
- **Free:** Can't compete here (we give value first)
- **$99/mo Pro:** Right price for SMBs ($1K-$100K MRR)
- **$249/mo Enterprise:** Still cheaper than hiring analyst

---

## Code Structure Guide

### Backend Structure

```
backend/
├── main.py                          # FastAPI app entry point
│   ├── @app.lifespan()             # APScheduler initialization
│   ├── Mount 18+ routers           # All route groups
│   ├── @app.get("/")               # Root health check
│   └── Error handlers              # Global error handling
│
├── requirements.txt                 # 23 frozen dependencies
│
├── Procfile                         # Render deployment config
│
├── ai/
│   ├── __init__.py
│   ├── nl_to_sql.py               # PRIMARY: NL→SQL via Claude
│   └── nl_to_sql_fixed.py         # BACKUP: Alternative implementation
│       └── Uses Anthropic API to convert natural language to SQL
│
├── db/
│   ├── __init__.py
│   └── snowflake_client.py        # Optional Snowflake connection
│       └── Wraps snowflake-connector-python
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                     # Authentication (primary)
│   ├── auth_clean.py               # Cleaned up version
│   ├── auth_routes_minimal.py      # Minimal auth endpoints
│   ├── query.py                    # Query processing pipeline
│   ├── connections.py              # Platform connection management
│   ├── upload.py                   # File upload handling
│   ├── billing.py                  # Stripe billing (optional)
│   └── ...13+ others               # Additional business logic
│
├── data/
│   ├── .gitkeep                    # Marks persistent directory
│   └── clariq.db                   # SQLite database (created at runtime)
│
└── shopify_sync.py                 # Background sync job for Shopify
```

### Frontend Structure

```
index.html                           # 720+ lines, all-in-one
├── <head>
│   ├── Meta tags
│   ├── Favicon SVG
│   └── <style> - All CSS
│       ├── CSS Variables (--brand, --ink, --soft, etc)
│       ├── .splash, .intro animations (keyframes)
│       ├── .gradient-bg, .nav, .hero styling
│       ├── .platforms, .globe, .stories sections
│       ├── .pricing, .trust, .cta sections
│       ├── .modal styling
│       ├── .page-wrapper system for multi-page routing
│       └── Responsive media queries @900px
│
└── <body>
    ├── .splash - Click to enter (fixed position, z-index 1001)
    ├── .intro - Animated bars (fixed position, z-index 1000)
    │
    ├── .page-wrapper#page-home (ACTIVE by default)
    │   ├── .gradient-bg
    │   │   ├── nav - Logo, nav links, buttons
    │   │   ├── .hero - Main headline + CTA
    │   │   └── .logos-bar - Marquee animation
    │   ├── .platforms - 8 e-commerce icons (clickable)
    │   ├── .trust - Security metrics
    │   ├── .pricing - 3 tier cards (clickable)
    │   ├── .cta-f - Final CTA
    │   └── .foot - Footer
    │
    ├── .page-wrapper#page-product
    │   ├── nav
    │   ├── Hero section
    │   ├── Content sections (Ask in English, Connect Platforms, etc)
    │   └── .foot
    │
    ├── .page-wrapper#page-pricing
    │   ├── nav
    │   ├── Pricing table
    │   └── .foot
    │
    ├── .page-wrapper#page-about
    ├── .page-wrapper#page-support
    ├── .page-wrapper#page-signin
    ├── .page-wrapper#page-signup
    │
    └── <script>
        ├── Splash/Intro animation logic
        ├── Audio context for piano chord
        ├── goToPage(pageName) router
        ├── goHome() shortcut
        ├── setPricing(mode) for pricing toggle
        ├── openModal/closeModal helpers
        ├── submitPilot() form handler
        └── Session storage for intro skip
```

---

## Scalability & Performance

### Current State
- **Database:** SQLite on Render filesystem
- **Workers:** 1 (single worker process)
- **Data Sync:** Sequential (shop by shop)
- **Query Execution:** Immediate (no caching)

### Bottlenecks
1. **SQLite Limitations:** ~10,000 concurrent queries max
2. **Single Worker:** Can't handle 100+ concurrent API requests
3. **Data Sync:** If 1000 stores need syncing, takes hours
4. **Query Performance:** Complex joins on large datasets slow

### Path to Scale (Phase 2+)

#### Immediate (1-3 months)
- [ ] Add query result caching (Redis)
- [ ] Increase workers to 4 (Render configuration)
- [ ] Add database indexing on common queries
- [ ] Implement rate limiting (Flask-Limiter)

#### Medium-term (3-6 months)
- [ ] Migrate to Snowflake for data warehouse
- [ ] Implement async data sync (concurrent jobs)
- [ ] Add distributed job queue (Celery)
- [ ] Implement query optimization layer

#### Long-term (6-12 months)
- [ ] Multi-region deployment
- [ ] Database read replicas
- [ ] Advanced caching (CDN for query results)
- [ ] Custom indexes for each business vertical
- [ ] Query result prediction (pre-compute common questions)

### Performance Targets

| Metric | Current | Target (Year 1) | Target (Year 2) |
|--------|---------|---|---|
| Query response time (p50) | 342ms | <200ms | <100ms |
| Query response time (p99) | 2500ms | <1000ms | <500ms |
| Data sync completion | 10 min for 1 store | <5 min for 10 stores | <2 min for 100 stores |
| Concurrent users | 10 | 1000 | 10000 |
| Uptime SLA | 99.5% | 99.9% | 99.99% |

---

## Future Roadmap

### Phase 2 (Next 3 months)
- [ ] Advanced analytics dashboard with visualizations
- [ ] Custom report generation and scheduling
- [ ] Multi-user team collaboration
- [ ] Mobile app (iOS/Android)
- [ ] Snowflake integration for enterprise data warehousing
- [ ] API for third-party integrations
- [ ] Slack bot ("@clariq what's my AOV?")

### Phase 3 (3-6 months)
- [ ] Predictive analytics ("Revenue forecast for next quarter")
- [ ] Automated alerts ("Product X out of stock", "Churn risk customer")
- [ ] White-label offering for platforms
- [ ] Advanced ML for customer segmentation
- [ ] Competitor benchmarking
- [ ] Industry trend reports

### Phase 4 (6-12 months)
- [ ] Action automation ("Auto-create discount if sales drop")
- [ ] AI marketing optimization
- [ ] Inventory optimization engine
- [ ] Pricing optimization
- [ ] Supply chain visibility
- [ ] Global expansion (localized for EU, APAC, LATAM)

### Phase 5+ (Year 2+)
- [ ] AI agent that manages your store automatically
- [ ] Fulfillment center integration
- [ ] 3PL management
- [ ] Cross-border trading optimization
- [ ] Enterprise data platform

---

## Key Metrics to Track

### Product Metrics
- **Questions asked:** Daily active users × questions per user
- **Query execution time:** P50, P99 latencies
- **Insight quality:** User feedback rating
- **Feature adoption:** % of users using each feature

### Business Metrics
- **User Acquisition:** How many signups per day?
- **Trial Conversion:** % of 7-day trial → paid customer
- **Monthly Recurring Revenue (MRR):** Total subscription revenue
- **Churn Rate:** % of customers canceling per month
- **Customer Lifetime Value:** How much does average customer spend?

### Technical Metrics
- **System Uptime:** % of time API is responding
- **API Response Time:** Avg latency per endpoint
- **Data Sync Reliability:** % of syncs that complete successfully
- **Database Query Performance:** Slow query log analysis

---

## Summary for Technical Onboarding

**What You're Building:**
An AI-powered platform that lets e-commerce sellers understand their data by asking natural language questions instead of learning SQL or juggling dashboards.

**Why It Matters:**
- E-commerce sellers waste 8+ hours/week on data gathering
- Existing solutions are expensive ($300+/month) and hard to use
- Clariq makes analytics accessible to everyone

**How It Works:**
1. User asks: "Which products are trending?"
2. AI converts to SQL automatically
3. Query your connected store data
4. Return results + insights in <3 seconds

**Current State:**
- ✅ Landing page (beautiful, animated, multi-page)
- ✅ API backend (FastAPI, 18+ routes)
- ✅ Multi-platform support (7 e-commerce platforms)
- ✅ Deployed to production (Render)
- ✅ Domain configured (tryclariq.com)
- ✅ Basic auth & queries working
- 🔄 Dashboard UI (basic version exists, needs enhancement)

**Your Role (As New Developer):**
- Understand the codebase
- Enhance frontend UI/UX
- Add missing features
- Scale infrastructure
- Improve query accuracy
- Build new integrations

---

**Welcome to the team! This is building the future of e-commerce analytics.** 🚀
