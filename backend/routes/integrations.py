"""
Integration Routes for Slack, Google Sheets, Shopify Webhooks
"""

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Dict, List, Optional
from services.slack_integration import slack_service
from services.google_sheets_integration import sheets_service
from services.shopify_webhook import shopify_webhook
from db.export_service import export_to_csv, export_to_excel, get_pilot_export_data, get_action_export_data
from db.advanced_analytics import advanced_analytics

router = APIRouter()


class SlackAlertRequest(BaseModel):
    title: str
    message: str
    severity: str = "info"


class WebhookPayload(BaseModel):
    data: Dict
    store_id: str


@router.get("/status")
async def get_integration_status() -> Dict:
    """Check status of all integrations"""
    return {
        'slack': {
            'configured': slack_service.is_configured(),
            'status': 'ready' if slack_service.is_configured() else 'not_configured'
        },
        'google_sheets': {
            'configured': sheets_service.is_configured(),
            'status': 'ready' if sheets_service.is_configured() else 'not_configured'
        },
        'shopify_webhooks': {
            'configured': bool(shopify_webhook.webhook_secret),
            'status': 'ready' if shopify_webhook.webhook_secret else 'not_configured'
        }
    }


# ===== SLACK INTEGRATION =====

@router.post("/slack/alert")
async def send_slack_alert(request: SlackAlertRequest) -> Dict:
    """Send alert to Slack"""
    if not slack_service.is_configured():
        raise HTTPException(status_code=400, detail="Slack not configured")
    
    return slack_service.send_alert(
        request.title,
        request.message,
        request.severity
    )


@router.post("/slack/milestone/{pilot_id}")
async def send_milestone_to_slack(pilot_id: int, milestone_key: str) -> Dict:
    """Send milestone notification to Slack"""
    from db.pilots_db import get_pilot
    from db.alert_manager import alert_manager
    
    pilot = get_pilot(pilot_id)
    if not pilot:
        raise HTTPException(status_code=404, detail="Pilot not found")
    
    milestones = alert_manager.MILESTONES.get(milestone_key, {})
    if not milestones:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    # Get current achievement
    roi_data = alert_manager._calculate_pilot_metrics(pilot_id)
    
    return slack_service.send_milestone_alert(
        pilot.get('name', 'Unknown'),
        pilot.get('store_name', 'Unknown'),
        milestones.get('title', milestone_key),
        milestones.get('emoji', '🎯'),
        roi_data.get('value', 0),
        milestones.get('threshold', 0)
    )


@router.post("/slack/pilot-report/{pilot_id}")
async def send_pilot_report_to_slack(pilot_id: int) -> Dict:
    """Send pilot performance report to Slack"""
    from db.pilots_db import get_pilot
    from db.roi_calc import calculate_pilot_roi
    from db.revenue_calc import calculate_revenue
    
    pilot = get_pilot(pilot_id)
    if not pilot:
        raise HTTPException(status_code=404, detail="Pilot not found")
    
    roi_data = calculate_pilot_roi(pilot_id)
    revenue = calculate_revenue(pilot_id)
    
    metrics = {
        'revenue': revenue,
        'roi_percent': roi_data.get('roi_metrics', {}).get('roi_percent', 0),
        'reorder_count': roi_data.get('action_metrics', {}).get('reorder_count', 0),
        'roi_status': roi_data.get('roi_metrics', {}).get('roi_status', 'Unknown')
    }
    
    return slack_service.send_pilot_report(pilot.get('name', 'Unknown'), metrics)


@router.post("/slack/churn-warning/{pilot_id}")
async def send_churn_warning_to_slack(pilot_id: int) -> Dict:
    """Send churn risk warning to Slack"""
    from db.pilots_db import get_pilot
    
    pilot = get_pilot(pilot_id)
    if not pilot:
        raise HTTPException(status_code=404, detail="Pilot not found")
    
    churn = advanced_analytics.predict_churn_risk(pilot_id)
    
    return slack_service.send_churn_warning(
        pilot.get('name', 'Unknown'),
        churn.get('churn_probability', 0),
        churn.get('recommendation', 'Monitor pilot')
    )


# ===== GOOGLE SHEETS INTEGRATION =====

@router.post("/sheets/export-pilots")
async def export_pilots_to_sheets() -> Dict:
    """Export all pilots to Google Sheets"""
    if not sheets_service.is_configured():
        raise HTTPException(status_code=400, detail="Google Sheets not configured")
    
    pilots_data = get_pilot_export_data()
    return sheets_service.export_pilots(pilots_data)


@router.post("/sheets/export-actions")
async def export_actions_to_sheets() -> Dict:
    """Export all actions to Google Sheets"""
    if not sheets_service.is_configured():
        raise HTTPException(status_code=400, detail="Google Sheets not configured")
    
    actions_data = get_action_export_data()
    return sheets_service.export_actions(actions_data)


@router.post("/sheets/create-dashboard")
async def create_sheets_dashboard(dashboard_name: str = "CLARIQ Dashboard") -> Dict:
    """Create live dashboard in Google Sheets"""
    if not sheets_service.is_configured():
        raise HTTPException(status_code=400, detail="Google Sheets not configured")
    
    return sheets_service.create_live_dashboard(dashboard_name)


@router.post("/sheets/sync-pilots")
async def auto_sync_pilots_to_sheets() -> Dict:
    """Automatically sync pilots to Google Sheets"""
    if not sheets_service.is_configured():
        return {'success': False, 'message': 'Google Sheets not configured'}
    
    result = export_pilots_to_sheets()
    
    return {
        'success': result.get('success', False),
        'message': f'Synced pilots to Google Sheets',
        'details': result
    }


# ===== SHOPIFY WEBHOOK INTEGRATION =====

@router.post("/shopify/webhook/orders")
async def handle_order_webhook(
    payload: Dict,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_shop_id: Optional[str] = Header(None)
) -> Dict:
    """Handle Shopify order webhook"""
    
    # Verify webhook signature
    # Note: Full verification would require reading raw body
    # This is a simplified implementation
    
    store_id = x_shopify_shop_id or 'unknown'
    return shopify_webhook.process_order_webhook(payload, store_id)


@router.post("/shopify/webhook/customers")
async def handle_customer_webhook(
    payload: Dict,
    x_shopify_shop_id: Optional[str] = Header(None)
) -> Dict:
    """Handle Shopify customer webhook"""
    store_id = x_shopify_shop_id or 'unknown'
    return shopify_webhook.process_customer_webhook(payload, store_id)


@router.post("/shopify/webhook/products")
async def handle_product_webhook(
    payload: Dict,
    x_shopify_shop_id: Optional[str] = Header(None)
) -> Dict:
    """Handle Shopify product webhook"""
    store_id = x_shopify_shop_id or 'unknown'
    return shopify_webhook.process_product_webhook(payload, store_id)


@router.get("/shopify/webhook/status")
async def get_shopify_status() -> Dict:
    """Get Shopify webhook status"""
    return shopify_webhook.get_stats()


@router.get("/shopify/webhook/pending")
async def get_pending_webhooks(topic: Optional[str] = None) -> Dict:
    """Get pending unprocessed webhooks"""
    webhooks = shopify_webhook.get_pending_webhooks(topic)
    return {
        'count': len(webhooks),
        'webhooks': webhooks
    }
