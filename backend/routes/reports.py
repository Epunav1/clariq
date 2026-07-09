from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import json
import os

from report_service import generate_weekly_summary_report, generate_cohort_report, format_email_html, format_email_body
from email_service import email_service
from db.pilots_db import list_pilots

router = APIRouter()


# Store report subscriptions (in production, use database)
SUBSCRIPTIONS_FILE = os.path.join(os.path.dirname(__file__), 'db', 'report_subscriptions.json')


def load_subscriptions():
    """Load report subscriptions from file."""
    if os.path.exists(SUBSCRIPTIONS_FILE):
        try:
            with open(SUBSCRIPTIONS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_subscriptions(subs):
    """Save report subscriptions to file."""
    os.makedirs(os.path.dirname(SUBSCRIPTIONS_FILE), exist_ok=True)
    with open(SUBSCRIPTIONS_FILE, 'w') as f:
        json.dump(subs, f, indent=2)


class ReportRequest(BaseModel):
    report_type: str  # 'weekly_summary' or 'cohort_analysis'
    recipient_email: EmailStr
    recipient_name: str = 'Team'


class ReportSubscription(BaseModel):
    recipient_email: EmailStr
    recipient_name: str = 'Team'
    report_types: List[str] = ['weekly_summary']  # Types to send
    frequency: str = 'weekly'  # 'daily', 'weekly', 'monthly'
    day_of_week: Optional[int] = 1  # 0=Monday, 1=Tuesday, etc. for weekly
    enabled: bool = True


@router.post('/generate-and-send')
async def generate_and_send_report(req: ReportRequest):
    """Generate a report and send it immediately via email."""
    try:
        if req.report_type == 'weekly_summary':
            report = generate_weekly_summary_report()
        elif req.report_type == 'cohort_analysis':
            report = generate_cohort_report()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown report type: {req.report_type}")
        
        # Format email
        subject = f"CLARIQ {req.report_type.replace('_', ' ').title()} Report"
        html_body = format_email_html(report, req.recipient_name)
        text_body = format_email_body(report, req.recipient_name)
        
        # Send email
        result = email_service.send_email(
            to_email=req.recipient_email,
            subject=subject,
            body=html_body,
            html=True
        )
        
        return {
            "success": result.get('success', False),
            "message": result.get('message', 'Report sent'),
            "report_type": req.report_type,
            "recipient": req.recipient_email,
            "sent_at": result.get('sent_at')
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/preview/{report_type}')
async def preview_report(report_type: str):
    """Preview a report without sending."""
    try:
        if report_type == 'weekly_summary':
            report = generate_weekly_summary_report()
        elif report_type == 'cohort_analysis':
            report = generate_cohort_report()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")
        
        return {
            "report": report,
            "html_preview": format_email_html(report, "Preview User")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/subscribe')
async def subscribe_to_reports(sub: ReportSubscription):
    """Subscribe to automated report emails."""
    try:
        subs = load_subscriptions()
        
        if not subs.get('subscriptions'):
            subs['subscriptions'] = []
        
        # Check if already subscribed
        existing = next(
            (s for s in subs['subscriptions'] if s['recipient_email'] == sub.recipient_email),
            None
        )
        
        sub_dict = {
            'recipient_email': sub.recipient_email,
            'recipient_name': sub.recipient_name,
            'report_types': sub.report_types,
            'frequency': sub.frequency,
            'day_of_week': sub.day_of_week,
            'enabled': sub.enabled,
            'subscribed_at': datetime.utcnow().isoformat()
        }
        
        if existing:
            # Update existing
            idx = subs['subscriptions'].index(existing)
            subs['subscriptions'][idx] = sub_dict
            action = 'updated'
        else:
            # Add new
            subs['subscriptions'].append(sub_dict)
            action = 'added'
        
        save_subscriptions(subs)
        
        return {
            "success": True,
            "message": f"Subscription {action}",
            "subscription": sub_dict
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/unsubscribe/{email}')
async def unsubscribe_from_reports(email: str):
    """Unsubscribe from automated reports."""
    try:
        subs = load_subscriptions()
        
        initial_count = len(subs.get('subscriptions', []))
        subs['subscriptions'] = [
            s for s in subs.get('subscriptions', [])
            if s['recipient_email'] != email
        ]
        
        if len(subs['subscriptions']) < initial_count:
            save_subscriptions(subs)
            return {
                "success": True,
                "message": f"Unsubscribed {email} from reports"
            }
        else:
            return {
                "success": False,
                "message": f"No subscription found for {email}"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/subscriptions')
async def list_subscriptions():
    """List all report subscriptions."""
    try:
        subs = load_subscriptions()
        return {
            "subscriptions": subs.get('subscriptions', []),
            "count": len(subs.get('subscriptions', []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/send-scheduled')
async def send_scheduled_reports():
    """Send reports to all active subscriptions (called by scheduler)."""
    try:
        subs = load_subscriptions()
        sent_count = 0
        failed_count = 0
        
        from datetime import datetime
        today = datetime.utcnow().weekday()  # 0=Monday
        
        for sub in subs.get('subscriptions', []):
            if not sub.get('enabled', True):
                continue
            
            # Check frequency
            if sub.get('frequency') == 'weekly' and today != sub.get('day_of_week', 1):
                continue
            
            # Send each report type
            for report_type in sub.get('report_types', ['weekly_summary']):
                try:
                    if report_type == 'weekly_summary':
                        report = generate_weekly_summary_report()
                    elif report_type == 'cohort_analysis':
                        report = generate_cohort_report()
                    else:
                        continue
                    
                    subject = f"CLARIQ {report_type.replace('_', ' ').title()} - {datetime.utcnow().strftime('%Y-%m-%d')}"
                    html_body = format_email_html(report, sub.get('recipient_name', 'Team'))
                    
                    result = email_service.send_email(
                        to_email=sub['recipient_email'],
                        subject=subject,
                        body=html_body,
                        html=True
                    )
                    
                    if result.get('success'):
                        sent_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    continue
        
        return {
            "success": True,
            "sent": sent_count,
            "failed": failed_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
