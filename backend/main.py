from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="CLARIQ API",
    description="AI-native universal commerce intelligence platform",
    version="0.4.0"
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://tryclariq.netlify.app",
    "https://tryclariq.com",
    "https://www.tryclariq.com",
    "https://beautiful-halva-c6f6b6.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from routes.query import router as query_router
from routes.connections import router as connections_router
from routes.upload import router as upload_router
from routes.recommendations import router as recommend_router
from routes.pilot import router as pilot_router
from routes.pilot_analytics import router as pilot_analytics_router
from routes.actions import router as actions_router
from routes.sync import router as sync_router
from routes.webhooks import router as webhooks_router
from routes.reports import router as reports_router
from routes.roi import router as roi_router
from routes.export import router as export_router
from routes.performance import router as performance_router
from routes.alerts import router as alerts_router
from routes.analytics import router as analytics_router
from routes.integrations import router as integrations_router
from routes.billing import router as billing_router
from routes.feedback import router as feedback_router
from sync_scheduler import start_scheduler, stop_scheduler
# from routes.auth import router as auth_router

# Mount routers
app.include_router(query_router, prefix="/api")
app.include_router(connections_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(recommend_router, prefix="/api")
app.include_router(pilot_router, prefix="/api/pilot")
app.include_router(pilot_analytics_router, prefix="/api/pilot")
app.include_router(actions_router, prefix="/api/actions")
app.include_router(sync_router, prefix="/api/sync")
app.include_router(webhooks_router, prefix="/api/webhook")
app.include_router(reports_router, prefix="/api/reports")
app.include_router(roi_router, prefix="/api/roi")
app.include_router(export_router, prefix="/api/export")
app.include_router(performance_router, prefix="/api/performance")
app.include_router(alerts_router, prefix="/api/alerts")
app.include_router(analytics_router, prefix="/api/analytics")
app.include_router(integrations_router, prefix="/api/integrations")
app.include_router(billing_router, prefix="/api/billing")
app.include_router(feedback_router, prefix="/api")
# app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# Startup and shutdown events for background scheduler
@app.on_event("startup")
async def startup_event():
    """Start the background sync scheduler."""
    try:
        start_scheduler()
    except Exception as e:
        print(f"Warning: Could not start scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the background sync scheduler."""
    try:
        stop_scheduler()
    except Exception as e:
        print(f"Warning: Could not stop scheduler: {e}")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Check API health status."""
    return {
        "status": "ok",
        "service": "CLARIQ API",
        "version": "0.4.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Welcome to CLARIQ API."""
    return {
        "name": "CLARIQ",
        "description": "AI-native universal commerce intelligence platform",
        "version": "0.4.0",
        "status": "live",
        "endpoints": {
            "health": "/api/health",
            "query": "/api/ask, /api/query",
            "platforms": "/api/platforms",
            "connections": "/api/connections",
            "upload": "/api/upload/*",
            "auth": "/api/auth/*"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
