"""
Milestone alerts API endpoints.
Manage and send automated notifications for pilot milestones.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from db.alert_manager import alert_manager

router = APIRouter()


class AlertSubscription(BaseModel):
    email: EmailStr
    pilot_id: Optional[int] = None
    milestone_key: Optional[str] = None


@router.post('/check/{pilot_id}')
async def check_pilot_milestones(pilot_id: int):
    """Check pilot against milestones and create alerts if reached."""
    try:
        new_alerts = alert_manager.check_and_create_alerts(pilot_id)
        return {
            'pilot_id': pilot_id,
            'new_alerts': new_alerts,
            'count': len(new_alerts),
            'message': f'{len(new_alerts)} milestone(s) reached'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/pending')
async def get_pending_alerts():
    """Get all unsent milestone alerts."""
    try:
        alerts = alert_manager.get_pending_alerts()
        return {
            'alerts': alerts,
            'count': len(alerts),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/send/{alert_id}')
async def send_milestone_alert(alert_id: int, email: EmailStr, name: str = 'Team'):
    """Send a specific milestone alert."""
    try:
        result = alert_manager.send_alert(alert_id, email, name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/send-all')
async def send_all_pending_alerts(email: EmailStr, name: str = 'Team'):
    """Send all pending alerts to an email address."""
    try:
        result = alert_manager.send_all_pending_alerts(email, name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/pilot/{pilot_id}')
async def get_pilot_milestones(pilot_id: int):
    """Get milestone progress for a pilot."""
    try:
        milestones = alert_manager.get_pilot_milestones(pilot_id)
        if 'error' in milestones:
            raise HTTPException(status_code=404, detail=milestones['error'])
        return milestones
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/milestones')
async def get_all_milestones():
    """Get definition of all available milestones."""
    try:
        from db.alert_manager import MILESTONES
        
        milestones_list = []
        for key, def_dict in MILESTONES.items():
            milestones_list.append({
                'key': key,
                'title': def_dict['title'],
                'emoji': def_dict.get('emoji', '⭐'),
                'threshold': def_dict['threshold'],
                'type': def_dict.get('action') or def_dict.get('type', 'unknown'),
            })
        
        return {
            'milestones': milestones_list,
            'count': len(milestones_list),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/check-all')
async def check_all_pilots():
    """Check all pilots for milestone achievement."""
    try:
        from db.pilots_db import list_pilots
        
        pilots = list_pilots()
        total_checked = 0
        total_milestones_reached = 0
        
        for pilot in pilots:
            new_alerts = alert_manager.check_and_create_alerts(pilot['id'])
            total_checked += 1
            total_milestones_reached += len(new_alerts)
        
        return {
            'total_pilots_checked': total_checked,
            'total_milestones_reached': total_milestones_reached,
            'message': f'Checked {total_checked} pilots, found {total_milestones_reached} new milestones'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
