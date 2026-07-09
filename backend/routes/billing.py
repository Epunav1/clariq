"""
Billing Routes for Stripe Integration

Manage subscriptions, payments, and billing
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from services.stripe_billing import stripe_service

router = APIRouter()


class CreateSubscriptionRequest(BaseModel):
    user_id: str
    email: str
    name: str
    plan: str = "starter"


class UpgradePlanRequest(BaseModel):
    user_id: str
    new_plan: str


class CancelSubscriptionRequest(BaseModel):
    user_id: str


@router.get("/plans")
async def get_billing_plans() -> Dict:
    """Get all available billing plans"""
    return stripe_service.get_plans()


@router.post("/subscribe")
async def create_subscription(request: CreateSubscriptionRequest) -> Dict:
    """Create subscription for user"""
    return stripe_service.create_subscription(
        request.user_id,
        request.email,
        request.name,
        request.plan
    )


@router.get("/subscription/{user_id}")
async def get_subscription(user_id: str) -> Dict:
    """Get subscription details for user"""
    sub = stripe_service.get_subscription(user_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.post("/upgrade")
async def upgrade_subscription(request: UpgradePlanRequest) -> Dict:
    """Upgrade to higher plan"""
    return stripe_service.upgrade_plan(request.user_id, request.new_plan)


@router.post("/cancel")
async def cancel_subscription(request: CancelSubscriptionRequest) -> Dict:
    """Cancel subscription"""
    return stripe_service.cancel_subscription(request.user_id)


@router.get("/usage/{user_id}")
async def check_usage(user_id: str) -> Dict:
    """Check usage vs plan limits"""
    return stripe_service.check_usage(user_id)


@router.get("/invoices/{user_id}")
async def get_invoices(user_id: str, limit: int = 10) -> Dict:
    """Get invoice history"""
    invoices = stripe_service.get_invoices(user_id, limit)
    return {
        'user_id': user_id,
        'invoices': invoices,
        'count': len(invoices)
    }


@router.get("/pricing")
async def get_pricing() -> Dict:
    """Get pricing information"""
    plans = stripe_service.get_plans()
    return {
        'plans': plans['plans'],
        'features_by_plan': {
            'free': ['Up to 2 pilots', 'Basic reports', 'Email support'],
            'starter': ['Up to 10 pilots', 'Advanced ROI analytics', 'Custom exports', 'Priority support'],
            'professional': ['Up to 50 pilots', 'Predictive analytics', 'Integrations', 'Dedicated support'],
            'enterprise': ['Unlimited pilots', 'Custom features', 'SLA guarantee', '24/7 support']
        }
    }
