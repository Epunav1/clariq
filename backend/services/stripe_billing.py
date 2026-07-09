"""
Stripe Billing Integration for CLARIQ

Tiered pricing plans, subscription management, and invoicing
"""

import os
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import sqlite3
import stripe

logger = logging.getLogger(__name__)


class StripeService:
    """Stripe payment and subscription management"""
    
    # Pricing plans (in cents)
    PLANS = {
        'free': {
            'name': 'Free',
            'price': 0,
            'max_pilots': 2,
            'features': ['Basic analytics', 'Email alerts'],
            'description': 'Up to 2 pilots, basic features'
        },
        'starter': {
            'name': 'Starter',
            'price': 4900,  # $49/month
            'max_pilots': 10,
            'features': ['Advanced ROI analytics', 'Custom exports', 'Performance monitoring', 'Milestone alerts'],
            'description': 'Up to 10 pilots, advanced features'
        },
        'professional': {
            'name': 'Professional',
            'price': 9900,  # $99/month
            'max_pilots': 50,
            'features': ['All Starter features', 'Predictive analytics', 'Cohort analysis', 'Churn prediction', 'Slack integration'],
            'description': 'Up to 50 pilots, professional features'
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': 29900,  # $299/month
            'max_pilots': 500,
            'features': ['All Professional features', 'Dedicated support', 'Custom integrations', 'API access'],
            'description': 'Up to 500 pilots, enterprise features'
        }
    }
    
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
        self.db_path = 'data/clariq_billing.sqlite'
        self._init_db()
    
    def _init_db(self):
        """Initialize billing database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT UNIQUE,
                    stripe_customer_id TEXT UNIQUE,
                    stripe_subscription_id TEXT,
                    plan_type TEXT,
                    status TEXT,
                    current_period_start TIMESTAMP,
                    current_period_end TIMESTAMP,
                    cancel_at_period_end INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    stripe_invoice_id TEXT UNIQUE,
                    amount INTEGER,
                    status TEXT,
                    paid_date TIMESTAMP,
                    due_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES subscriptions(user_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    pilot_count INTEGER,
                    export_count INTEGER,
                    api_calls INTEGER,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES subscriptions(user_id)
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_sub ON subscriptions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_inv ON invoices(user_id)")
            conn.commit()
    
    def create_customer(self, user_id: str, email: str, name: str) -> Dict:
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'user_id': user_id}
            )
            
            return {
                'success': True,
                'customer_id': customer.id,
                'message': 'Customer created successfully'
            }
        except stripe.error.StripeError as e:
            logger.error(f'Stripe customer creation failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def create_subscription(self, user_id: str, email: str, name: str, 
                          plan_type: str = 'starter') -> Dict:
        """Create subscription for user"""
        if plan_type not in self.PLANS:
            return {'success': False, 'message': 'Invalid plan type'}
        
        plan = self.PLANS[plan_type]
        
        try:
            # Create customer if doesn't exist
            customer_result = stripe.Customer.search(
                query=f"email:'{email}'"
            )
            
            if customer_result.data:
                customer = customer_result.data[0]
            else:
                customer_resp = self.create_customer(user_id, email, name)
                if not customer_resp['success']:
                    return customer_resp
                customer = stripe.Customer.retrieve(customer_resp['customer_id'])
            
            # Create subscription
            if plan_type == 'free':
                # Free plan - no subscription needed
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO subscriptions
                        (user_id, stripe_customer_id, plan_type, status)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, customer.id, plan_type, 'active'))
                    conn.commit()
                
                return {
                    'success': True,
                    'plan': plan_type,
                    'message': 'Free plan activated'
                }
            else:
                # Paid plan - create Stripe subscription
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': plan['name'],
                                'description': plan['description']
                            },
                            'recurring': {
                                'interval': 'month',
                                'interval_count': 1
                            },
                            'unit_amount': plan['price']
                        }
                    }],
                    metadata={'user_id': user_id}
                )
                
                # Store subscription in database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO subscriptions
                        (user_id, stripe_customer_id, stripe_subscription_id, plan_type, status, 
                         current_period_start, current_period_end)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user_id,
                        customer.id,
                        subscription.id,
                        plan_type,
                        subscription.status,
                        datetime.fromtimestamp(subscription.current_period_start),
                        datetime.fromtimestamp(subscription.current_period_end)
                    ))
                    conn.commit()
                
                return {
                    'success': True,
                    'plan': plan_type,
                    'subscription_id': subscription.id,
                    'amount': plan['price'] / 100,
                    'message': f'Subscription created for {plan["name"]} plan'
                }
        except stripe.error.StripeError as e:
            logger.error(f'Subscription creation failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def upgrade_plan(self, user_id: str, new_plan: str) -> Dict:
        """Upgrade subscription to higher plan"""
        if new_plan not in self.PLANS:
            return {'success': False, 'message': 'Invalid plan type'}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                sub = conn.execute(
                    "SELECT stripe_subscription_id, plan_type FROM subscriptions WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
            
            if not sub:
                return {'success': False, 'message': 'Subscription not found'}
            
            stripe_sub_id, old_plan = sub
            
            # Update Stripe subscription
            new_plan_def = self.PLANS[new_plan]
            subscription = stripe.Subscription.retrieve(stripe_sub_id)
            
            subscription.items.data[0].delete()
            subscription.add_invoice_item({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': new_plan_def['name']},
                    'recurring': {'interval': 'month'},
                    'unit_amount': new_plan_def['price']
                }
            })
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE subscriptions SET plan_type = ? WHERE user_id = ?
                """, (new_plan, user_id))
                conn.commit()
            
            return {
                'success': True,
                'old_plan': old_plan,
                'new_plan': new_plan,
                'message': f'Plan upgraded from {old_plan} to {new_plan}'
            }
        except stripe.error.StripeError as e:
            logger.error(f'Plan upgrade failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def cancel_subscription(self, user_id: str) -> Dict:
        """Cancel subscription"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                sub = conn.execute(
                    "SELECT stripe_subscription_id FROM subscriptions WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
            
            if not sub:
                return {'success': False, 'message': 'Subscription not found'}
            
            stripe.Subscription.delete(sub[0])
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE subscriptions SET status = 'cancelled', cancel_at_period_end = 1
                    WHERE user_id = ?
                """, (user_id,))
                conn.commit()
            
            return {
                'success': True,
                'message': 'Subscription cancelled'
            }
        except stripe.error.StripeError as e:
            logger.error(f'Cancellation failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def get_subscription(self, user_id: str) -> Optional[Dict]:
        """Get subscription details"""
        with sqlite3.connect(self.db_path) as conn:
            sub = conn.execute("""
                SELECT user_id, plan_type, status, current_period_start, current_period_end
                FROM subscriptions WHERE user_id = ?
            """, (user_id,)).fetchone()
        
        if not sub:
            return None
        
        plan = self.PLANS.get(sub[1], {})
        
        return {
            'user_id': sub[0],
            'plan': sub[1],
            'status': sub[2],
            'period_start': sub[3],
            'period_end': sub[4],
            'max_pilots': plan.get('max_pilots', 0),
            'features': plan.get('features', []),
            'price': plan.get('price', 0) / 100
        }
    
    def check_usage(self, user_id: str) -> Dict:
        """Check usage vs plan limits"""
        from db.pilots_db import list_pilots
        
        sub = self.get_subscription(user_id)
        if not sub:
            return {'error': 'Subscription not found'}
        
        # Get pilot count for this user
        # Note: This assumes pilots are associated with users
        all_pilots = list_pilots()
        pilot_count = len(all_pilots)  # Simplified - would need user association
        
        max_pilots = sub['max_pilots']
        
        return {
            'user_id': user_id,
            'plan': sub['plan'],
            'pilots_used': pilot_count,
            'pilots_limit': max_pilots,
            'usage_percentage': (pilot_count / max_pilots * 100) if max_pilots > 0 else 0,
            'can_add_pilot': pilot_count < max_pilots,
            'features': sub['features']
        }
    
    def get_invoices(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get invoice history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                invoices = conn.execute("""
                    SELECT stripe_invoice_id, amount, status, paid_date, created_at
                    FROM invoices
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, limit)).fetchall()
            
            return [
                {
                    'invoice_id': i[0],
                    'amount': i[1] / 100,
                    'status': i[2],
                    'paid_date': i[3],
                    'created_at': i[4]
                }
                for i in invoices
            ]
        except Exception as e:
            logger.error(f'Invoice retrieval failed: {str(e)}')
            return []
    
    def get_plans(self) -> Dict:
        """Get all available plans"""
        plans_list = []
        for plan_type, plan_data in self.PLANS.items():
            plans_list.append({
                'id': plan_type,
                'name': plan_data['name'],
                'price': plan_data['price'] / 100,
                'max_pilots': plan_data['max_pilots'],
                'features': plan_data['features'],
                'description': plan_data['description']
            })
        
        return {
            'plans': plans_list,
            'currency': 'usd'
        }


# Global instance
stripe_service = StripeService()
