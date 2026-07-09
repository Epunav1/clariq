from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from db.actions_db import log_action, get_actions, count_actions

router = APIRouter()


class ActionRequest(BaseModel):
    action_type: str
    pilot_id: Optional[int] = None
    store_id: Optional[str] = None
    product_id: Optional[str] = None
    quantity: Optional[int] = None
    metadata: Optional[str] = None


@router.post('/log')
async def log_user_action(req: ActionRequest):
    try:
        rec = log_action(
            action_type=req.action_type,
            pilot_id=req.pilot_id,
            store_id=req.store_id,
            product_id=req.product_id,
            quantity=req.quantity,
            metadata=req.metadata
        )
        return {"message": "Action logged", "action": rec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/count/{action_type}')
async def count_by_action(action_type: str, pilot_id: Optional[int] = None):
    try:
        cnt = count_actions(action_type=action_type, pilot_id=pilot_id)
        return {"action_type": action_type, "pilot_id": pilot_id, "count": cnt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/list')
async def list_all_actions(action_type: Optional[str] = None, pilot_id: Optional[int] = None):
    try:
        acts = get_actions(action_type=action_type, pilot_id=pilot_id)
        return {"actions": acts, "count": len(acts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
