from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from db.pilots_db import add_pilot, list_pilots
from db.pilots_db import update_pilot_status
from db.pilots_db import get_pilot
from email_service import email_service

router = APIRouter()


class PilotRequest(BaseModel):
    name: str
    email: EmailStr
    store_name: str
    platform: Optional[str] = 'Shopify'
    notes: Optional[str] = ''


@router.post('/signup')
async def signup_pilot(req: PilotRequest):
    try:
        data = req.dict()
        rec = add_pilot(data)
        return {"message": "Application received", "applicant": rec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/send/{pilot_id}')
async def send_email(pilot_id: int, body: Optional[str] = None):
    try:
        p = get_pilot(pilot_id)
        if not p:
            raise HTTPException(status_code=404, detail='Pilot not found')
        
        # build email body
        if not body:
            body = f"Hello {p['name']},\n\nThanks for applying to the clariq 7-day pilot for {p['store_name']}. We're excited to get you started.\n\nNext steps:\n1) We'll schedule a 15-minute onboarding call to connect your store.\n2) We'll run a quick sync and prepare 3 action recommendations.\n3) We'll follow up with the pilot report at day 7.\n\nReply to this email to confirm availability for the onboarding call.\n\nBest,\nThe clariq team"
        
        # send via email service
        result = email_service.send_email(p['email'], 'clariq — Pilot onboarding', body)
        
        # mark as contacted if email sent
        if result['success']:
            rec = update_pilot_status(pilot_id, 'contacted')
            return {"message": "Email sent and pilot marked contacted", "pilot": rec, "email_result": result}
        else:
            return {"message": "Email failed", "pilot": p, "email_result": result, "sent": False}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/list')
async def list_applicants():
    try:
        return {"pilots": list_pilots()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/contact/{pilot_id}')
async def contact_pilot(pilot_id: int):
    try:
        p = get_pilot(pilot_id)
        if not p:
            raise HTTPException(status_code=404, detail='Pilot not found')
        
        # send the outreach email
        result = email_service.send_pilot_outreach_email(
            p['email'], 
            p['name'], 
            p['store_name']
        )
        
        # mark as contacted (whether email sent or not, for UX)
        rec = update_pilot_status(pilot_id, 'contacted')
        
        return {
            "message": "Pilot contacted and email sent" if result['success'] else "Pilot marked contacted (email delivery issue)",
            "pilot": rec,
            "email_result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/email/{pilot_id}')
async def preview_email(pilot_id: int):
    try:
        p = get_pilot(pilot_id)
        if not p:
            raise HTTPException(status_code=404, detail='Pilot not found')
        
        # generate preview using email service template
        subject = "Join clariq's 7-day pilot program — free"
        body = f"""Hi {p['name']},

Thank you for your interest in clariq's pilot program! We're excited to help {p['store_name']} boost revenue through better data insights.

Here's what you get in the 7-day pilot:
• Unlimited questions asked to clariq's AI
• Real-time insights across all your platforms
• Automatic reorder recommendations
• Full access to all features

No credit card required. Just let us know if you have any questions.

Ready to get started? Reply to this email or visit https://tryclariq.com/pilot

Best regards,
The clariq team

P.S. After 7 days, we'll share your results and discuss next steps."""
        
        return {"pilot": p, "email_preview": body}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/results-email/{pilot_id}')
async def send_results_email(pilot_id: int, reorder_count: int = 0, est_value: int = 0, days_active: int = 7):
    """Send pilot results summary email."""
    try:
        p = get_pilot(pilot_id)
        if not p:
            raise HTTPException(status_code=404, detail='Pilot not found')
        
        # send results email
        result = email_service.send_pilot_results_email(
            p['email'],
            p['name'],
            p['store_name'],
            reorder_count,
            est_value,
            days_active
        )
        
        return {
            "message": "Results email sent" if result['success'] else "Results email failed",
            "pilot": p,
            "email_result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/export')
async def export_pilots_csv():
    """Export all pilots as CSV."""
    try:
        pilots = list_pilots()
        
        # CSV header
        csv = "Name,Email,Store,Platform,Status,Contacted At,Created At\n"
        
        # CSV rows
        for p in pilots:
            name = (p.get('name') or '').replace('"', '""')
            email = (p.get('email') or '').replace('"', '""')
            store = (p.get('store_name') or '').replace('"', '""')
            platform = (p.get('platform') or '').replace('"', '""')
            status = (p.get('status') or '').replace('"', '""')
            contacted = (p.get('contacted_at') or '').replace('"', '""')
            created = (p.get('created_at') or '').replace('"', '""')
            
            csv += f'"{name}","{email}","{store}","{platform}","{status}","{contacted}","{created}"\n'
        
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(csv, headers={'Content-Disposition': 'attachment; filename=pilots.csv'})
