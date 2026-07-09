from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from db.pilots_db import add_pilot, list_pilots
from db.pilots_db import update_pilot_status
from db.pilots_db import get_pilot
from db.actions_db import count_actions
from db.revenue_calc import calculate_pilot_revenue
from email_service import email_service
from datetime import datetime

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/report/{pilot_id}')
async def export_pilot_pdf(pilot_id: int):
    """Export pilot results as PDF report."""
    try:
        from pdf_service import generate_pilot_report_pdf
        from fastapi.responses import StreamingResponse
        
        p = get_pilot(pilot_id)
        if not p:
            raise HTTPException(status_code=404, detail='Pilot not found')
        
        # Gather pilot metrics
        reorder_count = count_actions(action_type='reorder', pilot_id=pilot_id)
        discount_count = count_actions(action_type='discount', pilot_id=pilot_id)
        promotion_count = count_actions(action_type='promotion', pilot_id=pilot_id)
        query_count = count_actions(action_type='query', pilot_id=pilot_id)
        
        # Calculate days active
        days_active = 0
        if p['contacted_at']:
            try:
                contacted = datetime.fromisoformat(p['contacted_at'])
                days_active = (datetime.utcnow() - contacted).days
            except:
                days_active = 0
        
        # Get revenue data
        revenue_data = calculate_pilot_revenue(pilot_id)
        total_revenue = revenue_data.get('total_revenue', 0)
        
        # Calculate velocity
        velocity = 0
        if days_active > 0:
            velocity = round(reorder_count / days_active, 2)
        
        # Build pilot data for PDF
        pilot_data = {
            "pilot": {
                "id": p['id'],
                "name": p['name'],
                "email": p['email'],
                "store_name": p['store_name'],
                "contacted_at": p['contacted_at'],
                "created_at": p['created_at']
            },
            "metrics": {
                "reorder_count": reorder_count,
                "discount_count": discount_count,
                "promotion_count": promotion_count,
                "query_count": query_count,
                "days_active": days_active,
                "total_revenue": total_revenue,
                "reorder_velocity": velocity
            }
        }
        
        # Generate PDF
        pdf_buffer = generate_pilot_report_pdf(pilot_data)
        
        # Return as downloadable file
        filename = f"pilot-report-{p['name'].replace(' ', '-').lower()}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/complete/{pilot_id}')
async def complete_pilot(pilot_id: int):
    """Mark a pilot as completed."""
    try:
        p = get_pilot(pilot_id)
        if not p:
            raise HTTPException(status_code=404, detail='Pilot not found')
        
        now = datetime.utcnow().isoformat()
        update_pilot_status(pilot_id, 'completed', completed_at=now)
        
        # Fetch updated pilot
        updated_pilot = get_pilot(pilot_id)
        
        return {
            'success': True,
            'pilot': updated_pilot,
            'message': f'Pilot {p["name"]} marked as completed'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
