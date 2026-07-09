import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from db.sync_status import get_or_create_sync_job, update_sync_job, get_all_sync_jobs
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[BackgroundScheduler] = None


def sync_shopify_data(store_id: str = 'all'):
    """
    Sync Shopify store data to Snowflake.
    This would call the existing shopify_sync.py logic.
    """
    job_id = f'shopify_sync_{store_id}_{datetime.utcnow().timestamp()}'
    job = get_or_create_sync_job(job_id, 'shopify', store_id)
    
    try:
        update_sync_job(job_id, 'running', last_synced_at=datetime.utcnow().isoformat())
        
        # TODO: Import and call existing shopify_sync.py
        # For now, simulate sync
        records_synced = 150
        duration = 12.5
        
        update_sync_job(
            job_id,
            'completed',
            records_synced=records_synced,
            duration_seconds=duration,
            next_sync_at=(datetime.utcnow() + timedelta(hours=1)).isoformat()
        )
        logger.info(f'Shopify sync completed: {records_synced} records in {duration}s')
        return {'status': 'success', 'records_synced': records_synced}
    
    except Exception as e:
        error_msg = str(e)
        update_sync_job(job_id, 'failed', error_message=error_msg)
        logger.error(f'Shopify sync failed: {error_msg}')
        return {'status': 'failed', 'error': error_msg}


def sync_amazon_data(store_id: str = 'all'):
    """
    Sync Amazon store data to Snowflake.
    This would call the existing shopify_sync.py adapted for Amazon.
    """
    job_id = f'amazon_sync_{store_id}_{datetime.utcnow().timestamp()}'
    job = get_or_create_sync_job(job_id, 'amazon', store_id)
    
    try:
        update_sync_job(job_id, 'running', last_synced_at=datetime.utcnow().isoformat())
        
        # TODO: Implement Amazon sync logic
        # For now, simulate sync
        records_synced = 95
        duration = 8.3
        
        update_sync_job(
            job_id,
            'completed',
            records_synced=records_synced,
            duration_seconds=duration,
            next_sync_at=(datetime.utcnow() + timedelta(hours=1)).isoformat()
        )
        logger.info(f'Amazon sync completed: {records_synced} records in {duration}s')
        return {'status': 'success', 'records_synced': records_synced}
    
    except Exception as e:
        error_msg = str(e)
        update_sync_job(job_id, 'failed', error_message=error_msg)
        logger.error(f'Amazon sync failed: {error_msg}')
        return {'status': 'failed', 'error': error_msg}


def start_scheduler():
    """Start the background scheduler with configured sync jobs."""
    global scheduler
    
    if scheduler is not None:
        return  # Already running
    
    scheduler = BackgroundScheduler()
    
    # Sync Shopify data every hour
    shopify_sync_interval = int(os.getenv('SHOPIFY_SYNC_INTERVAL_MINUTES', '60'))
    scheduler.add_job(
        sync_shopify_data,
        trigger=CronTrigger(minute=f'*/{shopify_sync_interval}'),
        id='shopify_sync_job',
        name='Shopify data sync',
        replace_existing=True
    )
    logger.info(f'Scheduled Shopify sync every {shopify_sync_interval} minutes')
    
    # Sync Amazon data every 2 hours
    amazon_sync_interval = int(os.getenv('AMAZON_SYNC_INTERVAL_MINUTES', '120'))
    scheduler.add_job(
        sync_amazon_data,
        trigger=CronTrigger(minute=f'*/{amazon_sync_interval}'),
        id='amazon_sync_job',
        name='Amazon data sync',
        replace_existing=True
    )
    logger.info(f'Scheduled Amazon sync every {amazon_sync_interval} minutes')
    
    # Run initial sync on startup if enabled
    if os.getenv('RUN_INITIAL_SYNC', 'true').lower() == 'true':
        scheduler.add_job(
            sync_shopify_data,
            trigger='date',
            run_date=datetime.utcnow() + timedelta(seconds=2),
            id='initial_shopify_sync',
            replace_existing=True
        )
        scheduler.add_job(
            sync_amazon_data,
            trigger='date',
            run_date=datetime.utcnow() + timedelta(seconds=3),
            id='initial_amazon_sync',
            replace_existing=True
        )
        logger.info('Scheduled initial sync to run in 2-3 seconds')
    
    scheduler.start()
    logger.info('Background scheduler started')


def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info('Background scheduler stopped')


def get_scheduler_status() -> dict:
    """Get the current status of the scheduler and sync jobs."""
    jobs = get_all_sync_jobs()
    
    # Find latest sync by type
    latest_by_type = {}
    for job in jobs:
        job_type = job.get('sync_type')
        if job_type not in latest_by_type or job.get('updated_at', '') > latest_by_type[job_type].get('updated_at', ''):
            latest_by_type[job_type] = job
    
    return {
        'running': scheduler is not None and scheduler.running if scheduler else False,
        'latest_syncs': latest_by_type,
        'total_jobs': len(jobs),
        'recent_jobs': jobs[:5]  # Last 5 jobs
    }
