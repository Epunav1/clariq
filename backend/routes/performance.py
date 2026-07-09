"""
Performance monitoring API endpoints.
Provides system health, API metrics, and performance analytics.
"""

from fastapi import APIRouter, HTTPException
from db.performance_monitor import performance_monitor

router = APIRouter()


@router.get('/health')
async def get_system_health():
    """Get comprehensive system health report."""
    try:
        report = performance_monitor.get_full_health_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/api-metrics')
async def get_api_performance(hours: int = 24):
    """Get API performance metrics for last N hours."""
    try:
        metrics = performance_monitor.get_api_metrics(hours)
        return {
            'query_params': {'hours': hours},
            'metrics': metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/system')
async def get_system_performance(hours: int = 24):
    """Get system performance metrics for last N hours."""
    try:
        metrics = performance_monitor.get_system_metrics(hours)
        return {
            'query_params': {'hours': hours},
            'metrics': metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/database')
async def get_database_health():
    """Get database connectivity and health status."""
    try:
        health = performance_monitor.get_database_health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/sync')
async def get_sync_health():
    """Get sync job status and health."""
    try:
        sync = performance_monitor.get_sync_status()
        return sync
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/status')
async def get_status_summary():
    """Get quick status summary."""
    try:
        api = performance_monitor.get_api_metrics(1)  # Last hour
        system = performance_monitor.get_system_metrics(1)
        db = performance_monitor.get_database_health()
        sync = performance_monitor.get_sync_status()
        
        return {
            'status': performance_monitor._calculate_overall_status(),
            'summary': {
                'api_health': api.get('status', 'unknown'),
                'system_health': system.get('status', 'unknown'),
                'database_health': db.get('database', 'unknown'),
                'sync_health': sync.get('status', 'unknown'),
            },
            'quick_metrics': {
                'api_error_rate': api.get('error_rate_percent', 0),
                'cpu_percent': system.get('avg_cpu_percent', 0),
                'memory_percent': system.get('avg_memory_percent', 0),
                'pilots_total': db.get('pilots_count', 0),
                'sync_success_rate': sync.get('success_rate_percent', 0),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
