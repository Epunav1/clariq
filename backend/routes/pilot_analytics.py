from fastapi import APIRouter, HTTPException
from typing import Optional
from db.pilots_db import list_pilots, get_pilot
from db.actions_db import get_actions, count_actions
from datetime import datetime

router = APIRouter()


@router.get('/results')
async def get_pilot_results():
    """Get detailed pilot performance metrics."""
    try:
        pilots = list_pilots()
        
        # enrich each pilot with action counts and time metrics
        results = []
        for p in pilots:
            pilot_id = p['id']
            reorder_count = count_actions(action_type='reorder', pilot_id=pilot_id)
            
            # calc days active
            days_active = 0
            if p['contacted_at']:
                try:
                    contacted = datetime.fromisoformat(p['contacted_at'])
                    days_active = (datetime.utcnow() - contacted).days
                except:
                    days_active = 0
            
            # reorder velocity
            velocity = 0
            if days_active > 0:
                velocity = round(reorder_count / days_active, 2)
            
            results.append({
                "id": pilot_id,
                "name": p['name'],
                "email": p['email'],
                "store_name": p['store_name'],
                "platform": p['platform'],
                "status": p['status'],
                "contacted_at": p['contacted_at'],
                "created_at": p['created_at'],
                "days_active": days_active,
                "reorder_count": reorder_count,
                "reorder_velocity": velocity,  # reorders per day
                "est_value": reorder_count * 5,  # rough estimate: $5 per reorder action
            })
        
        # aggregate stats
        total_pilots = len(results)
        contacted = sum(1 for r in results if r['status'] == 'contacted')
        total_reorders = sum(r['reorder_count'] for r in results)
        avg_reorders = round(total_reorders / total_pilots, 2) if total_pilots > 0 else 0
        total_est_value = sum(r['est_value'] for r in results)
        
        return {
            "pilots": results,
            "summary": {
                "total_pilots": total_pilots,
                "contacted": contacted,
                "pending": total_pilots - contacted,
                "total_reorders": total_reorders,
                "avg_reorders_per_pilot": avg_reorders,
                "est_total_value": total_est_value,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
