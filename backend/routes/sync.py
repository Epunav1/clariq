from fastapi import APIRouter, HTTPException

try:
    from sync_scheduler import sync_shopify_data, sync_amazon_data, get_scheduler_status
    SCHEDULER_AVAILABLE = True
except ImportError as e:
    SCHEDULER_AVAILABLE = False
    import logging
    logging.warning(f"Scheduler not available: {str(e)}")

from db.sync_status import get_all_sync_jobs, get_sync_job

router = APIRouter()


@router.get('/status')
async def get_sync_status():
    """Get current sync scheduler status and recent job history."""
    if not SCHEDULER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    try:
        status = get_scheduler_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/jobs')
async def list_sync_jobs():
    """List all sync jobs with their status."""
    try:
        jobs = get_all_sync_jobs()
        return {
            "total": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/jobs/{job_id}')
async def get_job_details(job_id: str):
    """Get details of a specific sync job."""
    try:
        job = get_sync_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/shopify/now')
async def trigger_shopify_sync(store_id: str = 'all'):
    """Manually trigger a Shopify data sync."""
    if not SCHEDULER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    try:
        result = sync_shopify_data(store_id)
        if result['status'] == 'failed':
            raise HTTPException(status_code=500, detail=result.get('error', 'Sync failed'))
        return {
            "message": "Shopify sync triggered",
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/amazon/now')
async def trigger_amazon_sync(store_id: str = 'all'):
    """Manually trigger an Amazon data sync."""
    if not SCHEDULER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    try:
        result = sync_amazon_data(store_id)
        if result['status'] == 'failed':
            raise HTTPException(status_code=500, detail=result.get('error', 'Sync failed'))
        return {
            "message": "Amazon sync triggered",
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/all/now')
async def trigger_all_syncs():
    """Manually trigger all data syncs."""
    if not SCHEDULER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    try:
        shopify_result = sync_shopify_data()
        amazon_result = sync_amazon_data()
        
        failed = []
        if shopify_result['status'] == 'failed':
            failed.append(f"Shopify: {shopify_result.get('error')}")
        if amazon_result['status'] == 'failed':
            failed.append(f"Amazon: {amazon_result.get('error')}")
        
        if failed:
            raise HTTPException(status_code=500, detail='; '.join(failed))
        
        return {
            "message": "All syncs triggered",
            "shopify": shopify_result,
            "amazon": amazon_result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
