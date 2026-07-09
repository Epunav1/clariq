import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from db.sync_status import get_or_create_sync_job, update_sync_job, get_all_sync_jobs
from typing import Optional

try:
    from db.shopify_sync_wrapper import sync_all_shopify_stores
    SHOPIFY_SYNC_AVAILABLE = True
except ImportError:
    SHOPIFY_SYNC_AVAILABLE = False
    sync_all_shopify_stores = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[BackgroundScheduler] = None


def sync_shopify_data(store_id: str = 'all'):
    """
    Sync Shopify store data to Snowflake.
    Calls real Shopify API via the wrapper module.
    """
    if not SHOPIFY_SYNC_AVAILABLE:
        return {'status': 'failed', 'error': 'Shopify sync not available'}
    
    job_id = f'shopify_sync_{store_id}_{datetime.utcnow().timestamp()}'
    job = get_or_create_sync_job(job_id, 'shopify', store_id)
    
    try:
        update_sync_job(job_id, 'running', last_synced_at=datetime.utcnow().isoformat())
        
        # Call the real Shopify sync
        result = sync_all_shopify_stores()
        
        records_synced = result.get('total_records', 0)
        status_detail = result.get('status_details', '')
        
        update_sync_job(
            job_id,
            'success',
            records_synced=records_synced,
            duration_seconds=0,
            next_sync_at=(datetime.utcnow() + timedelta(hours=1)).isoformat()
        )
        logger.info(f'Shopify sync completed: {records_synced} records. {status_detail}')
        return {'status': 'success', 'records_synced': records_synced, 'detail': status_detail}
    
    except Exception as e:
        error_msg = str(e)
        update_sync_job(job_id, 'failed', error_message=error_msg)
        logger.error(f'Shopify sync failed: {error_msg}')
        return {'status': 'failed', 'error': error_msg}


def sync_amazon_data(store_id: str = 'all'):
    """
    Sync Amazon store data to Snowflake.
    Currently a placeholder - Amazon MWS/SP-API integration to be implemented.
    """
    job_id = f'amazon_sync_{store_id}_{datetime.utcnow().timestamp()}'
    job = get_or_create_sync_job(job_id, 'amazon', store_id)
    
    try:
        update_sync_job(job_id, 'running', last_synced_at=datetime.utcnow().isoformat())
        
        # TODO: Implement Amazon Selling Partner API integration
        # Placeholder for now - logs but doesn't actually sync
        logger.info(f'Amazon sync job created but not yet implemented (store_id={store_id})')
        
        records_synced = 0
        update_sync_job(
            job_id,
            'success',
            records_synced=records_synced,
            duration_seconds=0,
            next_sync_at=(datetime.utcnow() + timedelta(hours=2)).isoformat()
        )
        
        return {'status': 'pending', 'message': 'Amazon sync not yet implemented', 'records_synced': 0}
    
    except Exception as e:
        error_msg = str(e)
        update_sync_job(job_id, 'failed', error_message=error_msg)
        logger.error(f'Amazon sync failed: {error_msg}')
        return {'status': 'failed', 'error': error_msg}
    
    except Exception as e:
        error_msg = str(e)
        update_sync_job(job_id, 'failed', error_message=error_msg)
        logger.error(f'Amazon sync failed: {error_msg}')
        return {'status': 'failed', 'error': error_msg}


def send_scheduled_reports():
    """
    Send scheduled pilot program reports to subscribed recipients.
    This is called by the scheduler based on configured frequency.
    """
    try:
        from routes.reports import send_scheduled_reports as send_reports_impl
        result = send_reports_impl()
        logger.info(f'Scheduled reports sent: {result}')
        return result
    except Exception as e:
        logger.error(f'Failed to send scheduled reports: {e}')
        return {'status': 'failed', 'error': str(e)}


def check_pilot_milestones():
    """
    Check all pilots for milestone achievement.
    Runs periodically to detect and alert on milestones.
    """
    try:
        from db.alert_manager import alert_manager
        from db.pilots_db import list_pilots
        
        pilots = list_pilots()
        total_milestones = 0
        
        for pilot in pilots:
            new_alerts = alert_manager.check_and_create_alerts(pilot['id'])
            total_milestones += len(new_alerts)
        
        logger.info(f'Milestone check complete: {total_milestones} new milestones found')
        return {'status': 'success', 'milestones_found': total_milestones}
    except Exception as e:
        logger.error(f'Failed to check pilot milestones: {e}')
        return {'status': 'failed', 'error': str(e)}


def start_scheduler():
    """Start the background scheduler with configured sync jobs."""
    global scheduler
    
    if scheduler is not None:
        return  # Already running
    
    scheduler = BackgroundScheduler()
    
    # Sync Shopify data every hour (use IntervalTrigger for periods > 59 minutes)
    shopify_sync_interval = int(os.getenv('SHOPIFY_SYNC_INTERVAL_MINUTES', '60'))
    if shopify_sync_interval <= 59:
        trigger_shopify = CronTrigger(minute=f'*/{shopify_sync_interval}')
    else:
        trigger_shopify = IntervalTrigger(minutes=shopify_sync_interval)
    
    scheduler.add_job(
        sync_shopify_data,
        trigger=trigger_shopify,
        id='shopify_sync_job',
        name='Shopify data sync',
        replace_existing=True
    )
    logger.info(f'Scheduled Shopify sync every {shopify_sync_interval} minutes')
    
    # Sync Amazon data every 2 hours (use IntervalTrigger for periods > 59 minutes)
    amazon_sync_interval = int(os.getenv('AMAZON_SYNC_INTERVAL_MINUTES', '120'))
    if amazon_sync_interval <= 59:
        trigger_amazon = CronTrigger(minute=f'*/{amazon_sync_interval}')
    else:
        trigger_amazon = IntervalTrigger(minutes=amazon_sync_interval)
    
    scheduler.add_job(
        sync_amazon_data,
        trigger=trigger_amazon,
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
    
    # Send scheduled reports every Tuesday at 9 AM
    scheduler.add_job(
        send_scheduled_reports,
        trigger=CronTrigger(day_of_week='1', hour='9', minute='0'),  # Tuesday at 9 AM
        id='scheduled_reports_job',
        name='Send scheduled reports',
        replace_existing=True
    )
    logger.info('Scheduled report sending for Tuesdays at 9 AM UTC')
    
    # Check pilot milestones every 30 minutes
    scheduler.add_job(
        check_pilot_milestones,
        trigger=CronTrigger(minute='*/30'),  # Every 30 minutes
        id='check_milestones_job',
        name='Check pilot milestones',
        replace_existing=True
    )
    logger.info('Scheduled milestone checks every 30 minutes')
    
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
