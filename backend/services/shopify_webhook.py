"""
Shopify Webhook Integration for Real-Time Order Sync

Handles incoming Shopify webhooks for orders, customers, and products
"""

import os
import hmac
import hashlib
import json
from typing import Dict, Optional
import logging
from datetime import datetime
import sqlite3

logger = logging.getLogger(__name__)


class ShopifyWebhookHandler:
    """Handle incoming Shopify webhooks"""
    
    def __init__(self):
        self.webhook_secret = os.getenv('SHOPIFY_WEBHOOK_SECRET')
        self.db_path = 'data/shopify_webhooks.sqlite'
        self._init_db()
    
    def _init_db(self):
        """Initialize webhook tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    id INTEGER PRIMARY KEY,
                    topic TEXT,
                    store_id TEXT,
                    payload TEXT,
                    processed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_topic ON webhooks(topic)")
            conn.commit()
    
    def verify_webhook(self, request_headers: Dict, body: bytes) -> bool:
        """Verify Shopify webhook signature"""
        if not self.webhook_secret:
            logger.warning('SHOPIFY_WEBHOOK_SECRET not configured')
            return False
        
        hmac_header = request_headers.get('X-Shopify-Hmac-SHA256', '')
        
        try:
            hash_obj = hmac.new(
                self.webhook_secret.encode(),
                body,
                hashlib.sha256
            )
            expected_hmac = hash_obj.digest()
            expected_hmac_b64 = __import__('base64').b64encode(expected_hmac).decode()
            
            return hmac.compare_digest(hmac_header, expected_hmac_b64)
        except Exception as e:
            logger.error(f'Webhook verification failed: {str(e)}')
            return False
    
    def process_order_webhook(self, order_data: Dict, store_id: str) -> Dict:
        """Process incoming order from Shopify webhook"""
        try:
            order_id = order_data.get('id')
            order_number = order_data.get('order_number')
            total_price = float(order_data.get('total_price', 0))
            created_at = order_data.get('created_at')
            customer = order_data.get('customer', {})
            
            logger.info(f'Processing order {order_number} from {store_id}: ${total_price}')
            
            # Store webhook for processing
            self._store_webhook({
                'topic': 'orders/create',
                'store_id': store_id,
                'order_id': order_id,
                'order_number': order_number,
                'total_price': total_price,
                'customer_email': customer.get('email'),
                'customer_id': customer.get('id'),
                'created_at': created_at
            })
            
            return {
                'success': True,
                'message': f'Order {order_number} queued for processing',
                'order_id': order_id,
                'amount': total_price
            }
        except Exception as e:
            logger.error(f'Order webhook processing failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def process_customer_webhook(self, customer_data: Dict, store_id: str) -> Dict:
        """Process customer update from Shopify webhook"""
        try:
            customer_id = customer_data.get('id')
            email = customer_data.get('email')
            first_name = customer_data.get('first_name')
            last_name = customer_data.get('last_name')
            
            logger.info(f'Processing customer {email} from {store_id}')
            
            # Store webhook
            self._store_webhook({
                'topic': 'customers/update',
                'store_id': store_id,
                'customer_id': customer_id,
                'email': email,
                'name': f'{first_name} {last_name}'.strip()
            })
            
            return {
                'success': True,
                'message': f'Customer {email} queued for processing',
                'customer_id': customer_id
            }
        except Exception as e:
            logger.error(f'Customer webhook processing failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def process_product_webhook(self, product_data: Dict, store_id: str) -> Dict:
        """Process product update from Shopify webhook"""
        try:
            product_id = product_data.get('id')
            title = product_data.get('title')
            handle = product_data.get('handle')
            vendor = product_data.get('vendor')
            
            logger.info(f'Processing product {title} from {store_id}')
            
            # Store webhook
            self._store_webhook({
                'topic': 'products/update',
                'store_id': store_id,
                'product_id': product_id,
                'title': title,
                'handle': handle,
                'vendor': vendor
            })
            
            return {
                'success': True,
                'message': f'Product {title} queued for processing',
                'product_id': product_id
            }
        except Exception as e:
            logger.error(f'Product webhook processing failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def _store_webhook(self, webhook_data: Dict):
        """Store webhook data for processing"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO webhooks (topic, store_id, payload)
                VALUES (?, ?, ?)
            """, (
                webhook_data.get('topic'),
                webhook_data.get('store_id'),
                json.dumps(webhook_data)
            ))
            conn.commit()
    
    def get_pending_webhooks(self, topic: Optional[str] = None) -> list:
        """Get unprocessed webhooks"""
        with sqlite3.connect(self.db_path) as conn:
            if topic:
                rows = conn.execute("""
                    SELECT id, topic, payload FROM webhooks
                    WHERE processed = 0 AND topic = ?
                    ORDER BY created_at ASC
                """, (topic,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, topic, payload FROM webhooks
                    WHERE processed = 0
                    ORDER BY created_at ASC
                """).fetchall()
        
        return [
            {'id': r[0], 'topic': r[1], 'payload': json.loads(r[2])}
            for r in rows
        ]
    
    def mark_processed(self, webhook_id: int):
        """Mark webhook as processed"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE webhooks SET processed = 1 WHERE id = ?
            """, (webhook_id,))
            conn.commit()
    
    def get_stats(self) -> Dict:
        """Get webhook statistics"""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM webhooks").fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM webhooks WHERE processed = 0").fetchone()[0]
            by_topic = conn.execute("""
                SELECT topic, COUNT(*) as count
                FROM webhooks
                GROUP BY topic
            """).fetchall()
        
        return {
            'total_webhooks': total,
            'pending_webhooks': pending,
            'processed_webhooks': total - pending,
            'by_topic': {t[0]: t[1] for t in by_topic}
        }


# Global instance
shopify_webhook = ShopifyWebhookHandler()
