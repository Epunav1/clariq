from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional
from db.actions_db import log_action
from db.pilots_db import list_pilots
from db.connections_db import get_connection
import hmac
import hashlib
import base64
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_shopify_webhook(request_body: bytes, hmac_header: str, shared_secret: str) -> bool:
    """Verify the webhook came from Shopify"""
    try:
        hash_obj = hmac.new(
            shared_secret.encode('utf-8'),
            msg=request_body,
            digestmod=hashlib.sha256
        )
        computed_hmac = base64.b64encode(hash_obj.digest()).decode()
        return hmac.compare_digest(computed_hmac, hmac_header)
    except Exception as e:
        logger.error(f"Webhook verification error: {e}")
        return False


@router.post('/shopify/order')
async def handle_shopify_order_webhook(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None)
):
    """
    Handle Shopify order creation webhooks.
    Logs reorder actions for customers linked to pilots.
    """
    try:
        # Get request body
        body = await request.body()
        
        # Verify webhook signature if secret available
        shared_secret = "YOUR_SHOPIFY_WEBHOOK_SECRET"  # Should be in env vars
        if x_shopify_hmac_sha256 and not verify_shopify_webhook(body, x_shopify_hmac_sha256, shared_secret):
            logger.warning("Webhook verification failed")
            return {"success": False, "message": "Verification failed"}
        
        # Parse JSON
        webhook_data = json.loads(body)
        
        # Extract order info
        order_id = webhook_data.get('id')
        customer_id = webhook_data.get('customer', {}).get('id')
        customer_email = webhook_data.get('customer', {}).get('email')
        total_price = float(webhook_data.get('total_price', 0))
        shop_domain = request.headers.get('X-Shopify-Shop-Api-Version', '').split('/')[0]
        
        if not order_id or not customer_id:
            return {"success": False, "message": "Missing order or customer ID"}
        
        # Find connection for this shop
        connections = list_pilots()  # Get all pilots to cross-reference
        
        # Check if this customer is a pilot
        pilot = None
        for p in connections:
            if p.get('email') == customer_email:
                pilot = p
                break
        
        if not pilot:
            # Customer not a pilot, still log but don't associate
            return {"success": True, "message": "Order received for non-pilot customer", "logged": False}
        
        # Log reorder action
        action = log_action({
            'action_type': 'reorder',
            'pilot_id': pilot['id'],
            'store_id': shop_domain,
            'product_id': None,
            'quantity': len(webhook_data.get('line_items', [])),
            'metadata': json.dumps({
                'order_id': order_id,
                'customer_id': customer_id,
                'total_price': total_price,
                'source': 'webhook'
            })
        })
        
        logger.info(f"Logged reorder for pilot {pilot['id']} from webhook")
        
        return {
            "success": True,
            "message": "Order logged as reorder",
            "action_id": action['id'],
            "pilot_id": pilot['id']
        }
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {e}")
        return {"success": False, "message": "Invalid JSON"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"success": False, "message": str(e)}


@router.post('/generic/action')
async def handle_generic_action_webhook(request: Request):
    """
    Generic webhook endpoint for custom action logging.
    Accepts: pilot_id, action_type, metadata
    """
    try:
        data = await request.json()
        
        action_type = data.get('action_type')
        pilot_id = data.get('pilot_id')
        metadata = data.get('metadata', {})
        
        if not action_type or not pilot_id:
            raise HTTPException(status_code=400, detail="Missing action_type or pilot_id")
        
        # Log action
        action = log_action({
            'action_type': action_type,
            'pilot_id': pilot_id,
            'store_id': data.get('store_id'),
            'product_id': data.get('product_id'),
            'quantity': data.get('quantity', 1),
            'metadata': json.dumps(metadata) if metadata else None
        })
        
        logger.info(f"Logged {action_type} for pilot {pilot_id} via webhook")
        
        return {
            "success": True,
            "action_id": action['id'],
            "message": f"{action_type} logged for pilot"
        }
    
    except Exception as e:
        logger.error(f"Generic webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/register-webhook/{platform}')
async def register_webhook(platform: str):
    """
    Register webhook with platform (requires API credentials).
    This is informational only - actual registration happens in admin.
    """
    try:
        if platform == 'shopify':
            webhook_url = "https://your-domain/api/webhook/shopify/order"
            events = ["orders/create", "orders/paid"]
            return {
                "success": True,
                "message": f"Register this webhook in Shopify admin",
                "details": {
                    "url": webhook_url,
                    "events": events,
                    "format": "json"
                }
            }
        elif platform == 'generic':
            webhook_url = "https://your-domain/api/webhook/generic/action"
            return {
                "success": True,
                "message": f"Generic webhook endpoint ready",
                "details": {
                    "url": webhook_url,
                    "method": "POST",
                    "body_schema": {
                        "action_type": "string (required)",
                        "pilot_id": "integer (required)",
                        "store_id": "string (optional)",
                        "product_id": "string (optional)",
                        "quantity": "integer (optional)",
                        "metadata": "object (optional)"
                    }
                }
            }
        else:
            return {"success": False, "message": f"Platform {platform} not supported"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
