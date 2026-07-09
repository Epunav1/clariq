from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from db.pilots_db import add_pilot, list_pilots
from db.pilots_db import update_pilot_status
from db.pilots_db import get_pilot
from db.pilots_db import record_email_send
import os
import smtplib
from email.message import EmailMessage

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
            body = f"Hello {p['name']},\n\nThanks for applying to the clariq 7-day pilot for {p['store_name']}. We'll schedule a 15-minute onboarding call. Reply with your availability.\n\nBest,\nThe clariq team"

        # send via SMTP if configured, otherwise log
        mail_host = os.environ.get('MAIL_HOST')
        mail_port = int(os.environ.get('MAIL_PORT', '587')) if os.environ.get('MAIL_PORT') else None
        mail_user = os.environ.get('MAIL_USER')
        mail_pass = os.environ.get('MAIL_PASS')
        mail_from = os.environ.get('MAIL_FROM') or (mail_user or 'noreply@clariq.ai')

        sent = False
        send_error = None
        if mail_host and mail_user and mail_pass:
            try:
                msg = EmailMessage()
                msg['Subject'] = 'clariq — Pilot onboarding'
                msg['From'] = mail_from
                msg['To'] = p['email']
                msg.set_content(body)
                with smtplib.SMTP(mail_host, mail_port or 587) as s:
                    s.starttls()
                    s.login(mail_user, mail_pass)
                    s.send_message(msg)
                sent = True
            except Exception as e:
                send_error = str(e)
        else:
            # fallback: log to stdout (or a file in production)
            print('--- PILOT EMAIL (logged) ---')
            print('To:', p['email'])
            print(body)
            print('--- END ---')
            sent = False

        # record send and mark contacted
        rec = record_email_send(pilot_id, body)

        return {"message": "Email processed", "sent": sent, "send_error": send_error, "pilot": rec}
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
        rec = update_pilot_status(pilot_id, 'contacted')
        if not rec:
            raise HTTPException(status_code=404, detail='Pilot not found')
        return {"message": "Pilot marked contacted", "pilot": rec}
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
        # simple outreach template
        tpl = f"Hello {p['name']},\n\nThanks for applying to the clariq 7-day pilot for {p['store_name']}. We're excited to get you started.\n\nNext steps:\n1) We'll schedule a 15-minute onboarding call to connect your store.\n2) We'll run a quick sync and prepare 3 action recommendations.\n3) We'll follow up with the pilot report at day 7.\n\nReply to this email to confirm availability for the onboarding call.\n\nBest,\nThe clariq team\n" 
        return {"pilot": p, "email_preview": tpl}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
